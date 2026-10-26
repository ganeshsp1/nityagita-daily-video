"""One-time helper, run on your own computer: signs in to the YouTube channel
and saves YT_CLIENT_ID, YT_CLIENT_SECRET and YT_REFRESH_TOKEN as secrets of
this GitHub repo (via the gh CLI), without printing them.

usage: python3 tools/get_youtube_token.py [--lang <code>] [owner/repo]
The OAuth client must be of type "Desktop app" in Google Cloud Console.
With --lang (e.g. --lang ta), pick that language's own channel; only
YT_REFRESH_TOKEN_TA is saved and the shared OAuth client is reused, so
YT_CLIENT_ID/YT_CLIENT_SECRET must be in your environment or typed again.
"""
import getpass
import http.server
import subprocess
import sys
import json
import os
import urllib.parse
import urllib.request
import webbrowser

# "youtube" covers uploading plus managing playlists and video visibility.
SCOPE = "https://www.googleapis.com/auth/youtube"
ARGS = sys.argv[1:]
LANG = ARGS.pop(ARGS.index("--lang") + 1).lower() if "--lang" in ARGS else ""
if LANG:
    ARGS.remove("--lang")
SUFFIX = f"_{LANG.upper()}" if LANG else ""  # per-language account, see publish/accounts.py
REPO = ARGS[0] if ARGS else "ganeshsp1/nityagita-daily-video"
client_id = os.environ.get("YT_CLIENT_ID") or input("OAuth client ID: ").strip()
client_secret = os.environ.get("YT_CLIENT_SECRET") or getpass.getpass("OAuth client secret (hidden): ").strip()
code_holder = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_holder["code"] = query.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Signed in. You can close this tab and return to the terminal.")

    def log_message(self, *args):
        pass


# Bind first on a free port picked by the OS (Desktop clients accept any
# loopback port), then build the redirect URL from it.
server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
REDIRECT = f"http://127.0.0.1:{server.server_address[1]}"

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code",
    "scope": SCOPE, "access_type": "offline", "prompt": "consent",
})
print(f"Opening the browser. Pick the YouTube channel that should post the {LANG or 'shared'} Shorts.")
webbrowser.open(auth_url)
server.handle_request()

body = urllib.parse.urlencode({
    "code": code_holder["code"], "client_id": client_id, "client_secret": client_secret,
    "redirect_uri": REDIRECT, "grant_type": "authorization_code",
}).encode()
with urllib.request.urlopen("https://oauth2.googleapis.com/token", body) as r:
    tokens = json.load(r)
values = [("YT_REFRESH_TOKEN" + SUFFIX, tokens["refresh_token"])]
if not LANG:
    values += [("YT_CLIENT_ID", client_id), ("YT_CLIENT_SECRET", client_secret)]
for name, value in values:
    subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value, text=True, check=True)
print(f"\nSaved {', '.join(n for n, _ in values)} to {REPO}.")
