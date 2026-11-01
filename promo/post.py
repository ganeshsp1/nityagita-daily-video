"""Posts the next promo video for each language, once per platform.

  python3 promo/post.py --base <public release URL> [--langs ml hi] \\
      [--platforms youtube instagram facebook threads] [--dry-run]

Videos are posted in the order of promo/scripts.json (ask, word, listen,
daily): each run posts, per language, the first one not yet on every
platform it has an account for. Platform posting reuses publish/*.py through
publish/accounts.py, so each language goes to its own account (or the shared
one). Links go to posted/promo.jsonl, one line per video and language, so
re-runs never post twice. Prints a summary; exits 1 if any post failed.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOG = ROOT / "posted" / "promo.jsonl"
POSTERS = {
    "youtube": "publish/youtube_upload.py",
    "instagram": "publish/instagram_post.py",
    "facebook": "publish/facebook_post.py",
    "threads": "publish/threads_post.py",
}


def load_log():
    entries = {}
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                entries[(e["video"], e["lang"])] = e
    return entries


def save_log(entries):
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries.values()),
                   encoding="utf-8")


def has_account(lang, platform):
    return subprocess.run([sys.executable, "publish/accounts.py", "check", lang, platform],
                          cwd=ROOT, capture_output=True).returncode == 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base", required=True, help="URL the release's videos download from")
    p.add_argument("--langs", nargs="*")
    p.add_argument("--platforms", nargs="*", default=list(POSTERS))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    spec = json.load(open(HERE / "scripts.json", encoding="utf-8"))
    order = list(spec["videos"])
    langs = args.langs or list(spec["videos"][order[0]]["lines"])
    log = load_log()
    failed = False
    for lang in langs:
        platforms = [pl for pl in args.platforms if has_account(lang, pl)]
        if not platforms:
            print(f"{lang}: no accounts; skipping")
            continue
        video = next((v for v in order
                      if any(not log.get((v, lang), {}).get(pl) for pl in platforms)), None)
        if video is None:
            print(f"{lang}: every promo is posted")
            continue
        entry = log.setdefault((video, lang), {"video": video, "lang": lang})
        meta = HERE / "meta" / f"{video}-{lang}.json"
        for pl in platforms:
            if entry.get(pl):
                continue
            target = f"{args.base.rstrip('/')}/{video}-{lang}.mp4"
            if pl == "youtube":
                # YouTube uploads the file itself.
                local = ROOT / "work" / "promo" / f"{video}-{lang}.mp4"
                if not local.exists():
                    subprocess.run(["curl", "-sSfL", "-o", str(local), "--create-dirs", target], check=True)
                target = str(local)
            if args.dry_run:
                print(f"{lang} {video} {pl}: would post {target}")
                continue
            r = subprocess.run([sys.executable, "publish/accounts.py", "run", lang, pl, "--",
                                sys.executable, POSTERS[pl], target, str(meta)],
                               cwd=ROOT, capture_output=True, text=True)
            url = r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else ""
            if url:
                entry[pl] = url
                print(f"{lang} {video} {pl}: {url}")
            else:
                failed = True
                print(f"::error::{lang} {video} {pl} failed: {r.stderr.strip()[-300:]}")
            save_log(log)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
