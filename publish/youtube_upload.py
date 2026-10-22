"""Uploads a generated video to YouTube as a Short (Data API v3, resumable).

usage: python3 publish/youtube_upload.py <video.mp4> <meta.json>
env:   YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (required)
       YT_PRIVACY: private | unlisted | public (default: public)
prints the video URL on success.
"""
import json
import os
import sys
import urllib.parse
import urllib.request


def access_token():
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", body, timeout=60) as r:
        return json.load(r)["access_token"]


def main():
    video_path, meta_path = sys.argv[1:3]
    meta = json.load(open(meta_path, encoding="utf-8"))
    token = access_token()
    size = os.path.getsize(video_path)

    resource = {
        "snippet": {
            "title": meta["youtube_title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": "27",  # Education
            "defaultLanguage": meta["lang"],
            "defaultAudioLanguage": meta["lang"],
        },
        "status": {
            "privacyStatus": os.environ.get("YT_PRIVACY", "public"),
            "selfDeclaredMadeForKids": False,
        },
    }
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        data=json.dumps(resource).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        method="POST",
    )
    with urllib.request.urlopen(init, timeout=60) as r:
        upload_url = r.headers["Location"]

    with open(video_path, "rb") as f:
        put = urllib.request.Request(upload_url, data=f.read(), method="PUT", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "video/mp4",
        })
    with urllib.request.urlopen(put, timeout=600) as r:
        video = json.load(r)

    print(f"https://youtube.com/shorts/{video['id']}")


if __name__ == "__main__":
    main()
