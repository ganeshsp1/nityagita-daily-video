"""One-time helper, run on your own computer: signs in to the YouTube channel
and prints the refresh token to save as the YT_REFRESH_TOKEN repo secret.

usage: YT_CLIENT_ID=... YT_CLIENT_SECRET=... python3 tools/get_youtube_token.py
The OAuth client must be of type "Desktop app" in Google Cloud Console.
"""
import http.server
import json
import os
import urllib.parse
import urllib.request
import webbrowser

PORT = 8765
REDIRECT = f"http://127.0.0.1:{PORT}"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
client_id = os.environ["YT_CLIENT_ID"]
client_secret = os.environ["YT_CLIENT_SECRET"]
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


auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code",
    "scope": SCOPE, "access_type": "offline", "prompt": "consent",
})
print("Opening the browser. Pick the YouTube channel that should post the Shorts.")
webbrowser.open(auth_url)
http.server.HTTPServer(("127.0.0.1", PORT), Handler).handle_request()

body = urllib.parse.urlencode({
    "code": code_holder["code"], "client_id": client_id, "client_secret": client_secret,
    "redirect_uri": REDIRECT, "grant_type": "authorization_code",
}).encode()
with urllib.request.urlopen("https://oauth2.googleapis.com/token", body) as r:
    tokens = json.load(r)
print("\nSave this as the YT_REFRESH_TOKEN secret (keep it private):\n")
print(tokens["refresh_token"])
