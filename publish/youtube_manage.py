"""YouTube housekeeping: per-language playlists and visibility.

usage:
  python3 publish/youtube_manage.py add <lang> <video_url_or_id>
      Adds the video to the language's playlist (created if missing).
  python3 publish/youtube_manage.py backfill <posted_log.jsonl>...
      For every logged upload: make it public and add it to its playlist.
env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (token needs the
     "youtube" scope; tools/get_youtube_token.py requests it).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "..", "generator", "config.json"), encoding="utf-8"))
API = "https://www.googleapis.com/youtube/v3"


def access_token():
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", body, timeout=60) as r:
        return json.load(r)["access_token"]


TOKEN = None
NEW_PLAYLISTS = set()


def call(method, path, params=None, body=None):
    url = f"{API}/{path}?{urllib.parse.urlencode(params or {})}"
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def video_id(value):
    return value.rstrip("/").split("/")[-1].split("?")[0]


def playlist_for(lang_code, cache={}):
    if lang_code in cache:
        return cache[lang_code]
    lang = CONFIG["languages"][lang_code]
    title = lang.get("playlist_title_override") or CONFIG["templates"]["playlist_title"].format(**lang)
    page = None
    while True:
        params = {"part": "snippet", "mine": "true", "maxResults": 50}
        if page:
            params["pageToken"] = page
        res = call("GET", "playlists", params)
        for pl in res.get("items", []):
            if pl["snippet"]["title"] == title:
                cache[lang_code] = pl["id"]
                return pl["id"]
        page = res.get("nextPageToken")
        if not page:
            break
    created = call("POST", "playlists", {"part": "snippet,status"}, {
        "snippet": {
            "title": title,
            "description": CONFIG["templates"]["playlist_description"].format(**lang),
            "defaultLanguage": lang_code,
        },
        "status": {"privacyStatus": "public"},
    })
    print(f"created playlist {title}")
    NEW_PLAYLISTS.add(created["id"])
    cache[lang_code] = created["id"]
    return created["id"]


def with_retry(fn, tries=6):
    """New playlists can return 404/409 for a few seconds; 5xx are transient."""
    for attempt in range(tries):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            if e.code not in (404, 409, 500, 503) or attempt == tries - 1:
                raise
            time.sleep(5)


def add_to_playlist(lang_code, vid):
    pid = playlist_for(lang_code)
    if pid not in NEW_PLAYLISTS:  # a new playlist is empty; nothing to check
        existing = with_retry(lambda: call("GET", "playlistItems", {
            "part": "contentDetails", "playlistId": pid, "videoId": vid, "maxResults": 1}))
        if existing.get("items"):
            return
    with_retry(lambda: call("POST", "playlistItems", {"part": "snippet"}, {
        "snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}},
    }))


def make_public(vid):
    res = call("GET", "videos", {"part": "status", "id": vid})
    if not res.get("items"):
        return
    status = res["items"][0]["status"]
    if status.get("privacyStatus") != "public":
        call("PUT", "videos", {"part": "status"}, {"id": vid, "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": status.get("selfDeclaredMadeForKids", False),
        }})
        print(f"made public: {vid}")


def main():
    global TOKEN
    TOKEN = access_token()
    cmd = sys.argv[1]
    try:
        if cmd == "add":
            add_to_playlist(sys.argv[2], video_id(sys.argv[3]))
        elif cmd == "backfill":
            for path in sys.argv[2:]:
                for line in open(path, encoding="utf-8"):
                    entry = json.loads(line)
                    if not entry.get("youtube"):
                        continue
                    vid = video_id(entry["youtube"])
                    make_public(vid)
                    add_to_playlist(entry["lang"], vid)
                    print(f"ok {entry['date']} {entry['lang']} {vid}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        sys.exit(f"YouTube API error {e.code}: {detail}")


if __name__ == "__main__":
    main()
