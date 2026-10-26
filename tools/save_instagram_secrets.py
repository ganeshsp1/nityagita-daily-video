"""One-time helper, run on your own computer after generating an Instagram
access token in the Meta app dashboard.

Checks the token with Instagram, looks up the account's user ID, and saves
IG_USER_ID and IG_ACCESS_TOKEN as secrets of this GitHub repo (via the gh CLI)
without printing them. Optionally also saves IG_REFRESH_PAT, the fine-grained
GitHub token the weekly refresh workflow uses to store renewed tokens.

usage: python3 tools/save_instagram_secrets.py [--lang <code>] [owner/repo]
With --lang (e.g. --lang ta) the token is for that language's own account and
is saved as IG_USER_ID_TA / IG_ACCESS_TOKEN_TA.
"""
import getpass
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ARGS = sys.argv[1:]
LANG = ARGS.pop(ARGS.index("--lang") + 1).lower() if "--lang" in ARGS else ""
if LANG:
    ARGS.remove("--lang")
SUFFIX = f"_{LANG.upper()}" if LANG else ""  # per-language account, see publish/accounts.py
REPO = ARGS[0] if ARGS else "ganeshsp1/nityagita-daily-video"


def save(name, value):
    subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value, text=True, check=True)


token = getpass.getpass("Instagram access token (hidden): ").strip()
query = urllib.parse.urlencode({"fields": "user_id,username,account_type", "access_token": token})
try:
    with urllib.request.urlopen(f"https://graph.instagram.com/me?{query}", timeout=60) as r:
        me = json.load(r)
except urllib.error.HTTPError as e:
    sys.exit(f"Instagram rejected the token: {e.read().decode(errors='replace')[:300]}")

print(f"Token works for @{me.get('username')} ({me.get('account_type')}).")
if me.get("account_type") not in ("BUSINESS", "MEDIA_CREATOR"):
    print("Warning: switch the account to a Professional (Creator) account before posting.")

save("IG_USER_ID" + SUFFIX, str(me["user_id"]))
save("IG_ACCESS_TOKEN" + SUFFIX, token)
print(f"Saved IG_USER_ID{SUFFIX} and IG_ACCESS_TOKEN{SUFFIX} to {REPO}.")

pat = getpass.getpass(
    "Optional: fine-grained GitHub token for weekly auto-refresh "
    "(Enter to skip, hidden): ").strip()
if pat:
    save("IG_REFRESH_PAT", pat)
    print(f"Saved IG_REFRESH_PAT to {REPO}.")
