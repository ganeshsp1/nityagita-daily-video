"""Publishes a generated video to Threads (Threads API).
The video must already be at a public URL.

usage: python3 publish/threads_post.py <public_video_url> <meta.json>
env:   THREADS_USER_ID, THREADS_TOKEN
prints the post permalink on success.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://graph.threads.net/v1.0"


def call(method, path, **params):
    params["access_token"] = os.environ["THREADS_TOKEN"]
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
    user = os.environ["THREADS_USER_ID"]

    container = call("POST", f"{user}/threads", media_type="VIDEO", video_url=video_url,
                     text=meta["threads_text"])["id"]
    for _ in range(60):
        status = call("GET", container, fields="status,error_message")
        if status.get("status") == "FINISHED":
            break
        if status.get("status") in ("ERROR", "EXPIRED"):
            sys.exit(f"Threads could not process the video: {status}")
        time.sleep(10)
    else:
        sys.exit("Timed out waiting for Threads to process the video")
    post_id = call("POST", f"{user}/threads_publish", creation_id=container)["id"]
    print(call("GET", post_id, fields="permalink").get("permalink", post_id))


if __name__ == "__main__":
    main()
