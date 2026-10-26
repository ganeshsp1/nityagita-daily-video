"""One-time helper, run on your own computer. Saves Facebook Page and/or
Threads credentials as secrets of this GitHub repo without printing them.

usage: python3 tools/save_meta_secrets.py facebook|threads [--lang <code>] [owner/repo]
With --lang (e.g. --lang ta) the secrets are for that language's own Page or
Threads account and get a _TA suffix.

facebook: asks for the Meta app ID + secret and a user token from Graph API
  Explorer (permissions: pages_show_list, pages_read_engagement,
  pages_manage_posts). Exchanges it for a long-lived token, lists your Pages,
  and saves the chosen Page's ID and Page token (which does not expire).
threads: asks for a Threads user token (Threads use case → generate token),
  checks it, and saves THREADS_USER_ID and THREADS_TOKEN.
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
MODE = ARGS[0] if ARGS else ""
REPO = ARGS[1] if len(ARGS) > 1 else "ganeshsp1/nityagita-daily-video"


def save(name, value):
    subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value, text=True, check=True)


def get(url, **params):
    try:
        with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Rejected: {e.read().decode(errors='replace')[:300]}")


if MODE == "facebook":
    app_id = input("Meta app ID: ").strip()
    app_secret = getpass.getpass("Meta app secret (hidden): ").strip()
    user_token = getpass.getpass("User token from Graph API Explorer (hidden): ").strip()
    long_user = get("https://graph.facebook.com/v23.0/oauth/access_token",
                    grant_type="fb_exchange_token", client_id=app_id,
                    client_secret=app_secret, fb_exchange_token=user_token)["access_token"]
    me = get("https://graph.facebook.com/v23.0/me", fields="id,name", metadata="1",
             access_token=long_user)
    if me.get("metadata", {}).get("type") == "page":
        sys.exit("That is a Page token. In Graph API Explorer set 'User or Page' to "
                 "'User Token', generate again, and re-run this helper.")
    pages = get("https://graph.facebook.com/v23.0/me/accounts",
                fields="id,name,access_token", access_token=long_user).get("data", [])
    if not pages:
        sys.exit("No Pages found. Make sure the token has pages_show_list and you selected the Page.")
    for i, pg in enumerate(pages, 1):
        print(f"  {i}. {pg['name']}")
    choice = pages[int(input("Which Page posts the Reels? Number: ").strip()) - 1]
    save("FB_PAGE_ID" + SUFFIX, choice["id"])
    save("FB_PAGE_TOKEN" + SUFFIX, choice["access_token"])
    print(f"Saved FB_PAGE_ID{SUFFIX} and FB_PAGE_TOKEN{SUFFIX} for '{choice['name']}' to {REPO}.")
elif MODE == "threads":
    token = getpass.getpass("Threads access token (hidden): ").strip()
    me = get("https://graph.threads.net/v1.0/me", fields="id,username", access_token=token)
    print(f"Token works for Threads @{me.get('username')}.")
    save("THREADS_USER_ID" + SUFFIX, me["id"])
    save("THREADS_TOKEN" + SUFFIX, token)
    print(f"Saved THREADS_USER_ID{SUFFIX} and THREADS_TOKEN{SUFFIX} to {REPO}.")
else:
    sys.exit(__doc__)
