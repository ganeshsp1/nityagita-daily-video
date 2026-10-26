"""Walks you through setting up one Instagram account per language, on your
own computer (macOS). It opens each page in Chrome and copies the next value
to the clipboard; you paste and click. It never logs in or clicks for you.

At the end of each language it asks for the account's token (hidden), checks
it belongs to the right account, saves IG_USER_ID_<LANG> / IG_ACCESS_TOKEN_<LANG>
as repo secrets, and can post the two latest videos as starter Reels.

usage: python3 tools/instagram_account_helper.py [lang ...] [--connect] [--repo owner/repo]
       no languages = every language not yet done (progress is remembered)
       --connect: account already created; only save its token and post starters
"""
import getpass
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CONFIG = json.load(open(os.path.join(ROOT, "generator", "config.json"), encoding="utf-8"))
PROGRESS = os.path.expanduser("~/.nityagita_instagram_accounts.json")
MAIN = "the_nityagita"
ORDER = ["hi", "ta", "te", "ml", "kn", "mr", "bn", "or"]  # English stays on the main account

args = sys.argv[1:]
REPO = args.pop(args.index("--repo") + 1) if "--repo" in args else "ganeshsp1/nityagita-daily-video"
if "--repo" in args:
    args.remove("--repo")
CONNECT_ONLY = "--connect" in args
if CONNECT_ONLY:
    args.remove("--connect")


def profile(code):
    lang = CONFIG["languages"][code]
    link = CONFIG["play_store_url"] + "&referrer=" + urllib.parse.quote(
        f"utm_source=instagram&utm_medium=bio&utm_campaign={code}")
    return {
        "handle": f"{MAIN}_{lang['name'].lower()}",
        "name": f"Gita {lang['name']} · {lang['app_title']}",
        "bio": f"🙏 {lang['gita']} · {lang['today_label']}\n"
               f"🕕 Daily 6 AM IST · Sanskrit + {lang['native_name']}\n"
               f"📲 {lang['download_app']} 👇",
        "link": link,
    }


def chrome(url):
    subprocess.run(["open", "-a", "Google Chrome", url], check=False)


def copy(text, what):
    subprocess.run(["pbcopy"], input=text, text=True, check=True)
    print(f"   📋 Copied {what}:")
    for line in text.splitlines():
        print(f"      {line}")


def wait(prompt="Done? Press Enter"):
    answer = input(f"   ↵ {prompt} (s = skip this language, q = quit): ").strip().lower()
    if answer == "q":
        sys.exit("Stopped. Run again to continue where you left off.")
    return answer != "s"


def step(n, title):
    print(f"\n── Step {n}: {title}")


def load_progress():
    try:
        return json.load(open(PROGRESS))
    except (OSError, ValueError):
        return {}


def save_progress(progress):
    json.dump(progress, open(PROGRESS, "w"), indent=1)


def ig(path, token, **params):
    params["access_token"] = token
    with urllib.request.urlopen(f"https://graph.instagram.com/{path}?{urllib.parse.urlencode(params)}",
                                timeout=60) as r:
        return json.load(r)


def latest_videos(code, count=2):
    """(video_url, caption) for the newest releases that have this language, oldest first."""
    lang = CONFIG["languages"][code]
    tags = subprocess.run(["gh", "release", "list", "-R", REPO, "--limit", "10", "--json", "tagName",
                           "-q", ".[].tagName"], capture_output=True, text=True, check=True).stdout.split()
    found = []
    for tag in tags:
        if not tag.startswith("video-"):
            continue
        body = subprocess.run(["gh", "release", "view", tag, "-R", REPO, "--json", "body", "-q", ".body"],
                              capture_output=True, text=True, check=True).stdout
        m = re.search(rf"^- {code}: (.+)$", body, re.M)
        if not m:
            continue
        ref = m.group(1).split("|")[0].replace(lang["gita"], "").strip()
        hashtags = lang["hashtags"].replace("#shorts", "").strip()
        caption = (f"🙏 {lang['today_label']} · {lang['gita']} {ref}\n\n"
                   f"📲 {lang['download_app']} – {lang['app_title']} (link in bio)\n\n{hashtags}")
        date = tag[len("video-"):]
        url = f"https://github.com/{REPO}/releases/download/{tag}/nityagita-{date}-{code}.mp4"
        found.append((url, caption))
        if len(found) == count:
            break
    return list(reversed(found))


def connect(code, p):
    token = getpass.getpass(f"   Paste the token for @{p['handle']} (hidden): ").strip()
    try:
        me = ig("me", token, fields="user_id,username,account_type")
    except urllib.error.HTTPError as e:
        print(f"   ✗ Instagram rejected the token: {e.read().decode(errors='replace')[:200]}")
        return False
    if me.get("username") != p["handle"]:
        print(f"   ✗ That token is for @{me.get('username')}, not @{p['handle']}. Generate it for the right account.")
        return False
    if me.get("account_type") not in ("BUSINESS", "MEDIA_CREATOR"):
        print("   ⚠ The account isn't professional yet; redo step 4 (Creator) before automation posts to it.")
    suffix = "_" + code.upper()
    for name, value in ((f"IG_USER_ID{suffix}", str(me["user_id"])), (f"IG_ACCESS_TOKEN{suffix}", token)):
        subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value, text=True, check=True)
    print(f"   ✓ Saved IG_USER_ID{suffix} and IG_ACCESS_TOKEN{suffix} to {REPO}.")

    if input("   Post the two latest videos as starter Reels now? [Y/n]: ").strip().lower() in ("", "y", "yes"):
        env = dict(os.environ, IG_USER_ID=str(me["user_id"]), IG_ACCESS_TOKEN=token)
        for url, caption in latest_videos(code):
            meta = os.path.join(os.environ.get("TMPDIR", "/tmp"), f"ig_starter_{code}.json")
            json.dump({"instagram_caption": caption}, open(meta, "w"), ensure_ascii=False)
            print("   ⏳ Posting (Instagram takes a minute to process each video)…")
            result = subprocess.run([sys.executable, os.path.join(ROOT, "publish", "instagram_post.py"), url, meta],
                                    env=env, capture_output=True, text=True)
            print(f"   ✓ {result.stdout.strip()}" if result.returncode == 0
                  else f"   ✗ Post failed: {(result.stderr or result.stdout).strip()[:300]}")
    return True


def setup(code, handle=None):
    p = profile(code)
    p["handle"] = handle or p["handle"]
    name = CONFIG["languages"][code]["name"]
    print(f"\n═══════ {name} · @{p['handle']} ═══════")
    if CONNECT_ONLY:
        step(5, "Save the token (copy it from the Meta app: Generate token)")
        chrome("https://developers.facebook.com/apps/")
        while not connect(code, p):
            if not wait("Press Enter to try the token again"):
                return None
        return p["handle"]

    step(1, "Create the account (Accounts Center → Add accounts → Add Instagram account → Create new account)")
    print(f"   Logged in as @{MAIN}. Opening Accounts Center.")
    chrome("https://accountscenter.instagram.com/profiles/")
    copy(p["name"], "Name")
    if not wait("Pasted the Name? Press Enter for the Username"):
        return None
    copy(p["handle"], "Username")
    print(f"   If it's taken, use another (e.g. nityagita.{name.lower()}) and type it below.")
    answer = input("   ↵ Submitted? Enter = created with this username, or type the one you used "
                   "(s = skip, q = quit): ").strip()
    if answer.lower() == "q":
        sys.exit("Stopped. Run again to continue where you left off.")
    if answer.lower() == "s":
        return None
    if answer:
        p["handle"] = answer.lstrip("@")

    step(2, f"Switch to @{p['handle']}")
    chrome("https://www.instagram.com/")
    print(f"   In Instagram: More (☰) → Switch accounts → @{p['handle']}.")
    if not wait():
        return None

    step(3, "Profile: bio, link, photo")
    chrome("https://www.instagram.com/accounts/edit/")
    copy(p["bio"], "Bio")
    if not wait("Pasted the Bio? Press Enter for the link"):
        return None
    copy(p["link"], "Link")
    print("   Paste it under Website/Links (if the web says links are mobile-only, add it later in the app).")
    print("   Set the same profile photo as the main account, then Submit.")
    if not wait():
        return None

    step(4, "Switch to a Creator account")
    chrome("https://www.instagram.com/accounts/convert_to_professional_account/")
    print("   Choose Creator → category Education. Skip connecting a Facebook Page.")
    if not wait():
        return None

    step(5, "Add the account to the Meta app and generate its token")
    chrome("https://developers.facebook.com/apps/")
    print("   Your app → Instagram → API setup with Instagram login → Generate access tokens →")
    print(f"   Add account → log in as @{p['handle']} (not @{MAIN}) → Generate token → Copy.")
    if not wait("Token copied? Press Enter to paste it"):
        return None
    while not connect(code, p):
        if not wait("Press Enter to try the token again"):
            return None
    return p["handle"]


def main():
    progress = load_progress()
    codes = args or [c for c in ORDER if c not in progress]
    if CONNECT_ONLY and not args:
        sys.exit("--connect needs the language code(s), e.g. --connect hi")
    unknown = [c for c in codes if c not in CONFIG["languages"]]
    if unknown:
        sys.exit(f"Unknown language codes: {' '.join(unknown)}")
    if not codes:
        sys.exit(f"All languages are done (see {PROGRESS}). Name a language to redo it.")
    print(f"Setting up: {' '.join(codes)}. Tip: 2–3 new accounts a day avoids Instagram's spam checks.")
    for i, code in enumerate(codes):
        handle = setup(code, progress.get(code))
        if handle:
            progress[code] = handle
            save_progress(progress)
            print(f"\n   ✅ {code} done. The next 06:00 IST run posts {code} to its own account.")
        if i + 1 < len(codes) and input("\nContinue with the next language? [Y/n]: ").strip().lower() not in ("", "y", "yes"):
            break
    left = [c for c in ORDER if c not in progress]
    print(f"\nDone so far: {' '.join(progress) or 'none'}. Still to do: {' '.join(left) or 'none'}.")


if __name__ == "__main__":
    main()
