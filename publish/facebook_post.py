"""Publishes a generated video as a Facebook Page Reel (Graph API video_reels).
The video must already be at a public URL.

usage: python3 publish/facebook_post.py <public_video_url> <meta.json>
env:   FB_PAGE_ID, FB_PAGE_TOKEN (Page access token with pages_manage_posts)
       FB_API_VERSION (default: v23.0)
prints the Reel URL on success.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = os.environ.get("FB_API_VERSION", "v23.0")
GRAPH = f"https://graph.facebook.com/{VERSION}"
PAGE = os.environ["FB_PAGE_ID"]
TOKEN = os.environ["FB_PAGE_TOKEN"]


def post(url, params=None, headers=None):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers=headers or {})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def get(path, **params):
    params["access_token"] = TOKEN
    with urllib.request.urlopen(f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}", timeout=60) as r:
        return json.load(r)


def main():
    video_url, meta_path = sys.argv[1:3]
    meta = json.load(open(meta_path, encoding="utf-8"))

    start = post(f"{GRAPH}/{PAGE}/video_reels", {"upload_phase": "start", "access_token": TOKEN})
    vid = start["video_id"]
    # Facebook fetches the hosted file itself.
    post(start["upload_url"], headers={"Authorization": f"OAuth {TOKEN}", "file_url": video_url})
    post(f"{GRAPH}/{PAGE}/video_reels", {
        "upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
        "description": meta["instagram_caption"], "access_token": TOKEN,
    })
    for _ in range(40):
        try:
            status = get(vid, fields="status").get("status", {})
        except urllib.error.HTTPError:
            # The publish call already succeeded; status reads can fail transiently.
            time.sleep(10)
            continue
        if status.get("video_status") in ("ready", "published") or \
                status.get("publishing_phase", {}).get("status") == "complete":
            break
        if status.get("video_status") == "error":
            sys.exit(f"Facebook could not process the video: {status}")
        time.sleep(10)
    print(f"https://www.facebook.com/reel/{vid}")


if __name__ == "__main__":
    main()
