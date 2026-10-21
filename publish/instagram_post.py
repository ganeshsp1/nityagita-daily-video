"""Publishes a generated video as an Instagram Reel (Instagram API with
Instagram Login). The video must already be at a public URL.

usage: python3 publish/instagram_post.py <public_video_url> <meta.json>
env:   IG_USER_ID, IG_ACCESS_TOKEN (required)
       IG_API_VERSION (default: v23.0)
prints the Reel permalink on success.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = f"https://graph.instagram.com/{os.environ.get('IG_API_VERSION', 'v23.0')}"


def call(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{API}/{path}?{data}")
    else:
        req = urllib.request.Request(f"{API}/{path}", data=data.encode(), method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    video_url, meta_path = sys.argv[1:3]
    meta = json.load(open(meta_path, encoding="utf-8"))
    user = os.environ["IG_USER_ID"]

    container = call("POST", f"{user}/media", media_type="REELS", video_url=video_url,
                     caption=meta["instagram_caption"], share_to_feed="true")["id"]

    # Instagram fetches and transcodes the video asynchronously.
    for _ in range(60):
        status = call("GET", container, fields="status_code,status").get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram could not process the video: {status}")
        time.sleep(10)
    else:
        sys.exit("Timed out waiting for Instagram to process the video")

    media_id = call("POST", f"{user}/media_publish", creation_id=container)["id"]
    print(call("GET", media_id, fields="permalink").get("permalink", media_id))


if __name__ == "__main__":
    main()
