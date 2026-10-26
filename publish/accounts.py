"""Picks the account each language posts to on each platform.

A secret named <NAME>_<LANG> (e.g. IG_ACCESS_TOKEN_TA) gives that language its
own account, overriding the shared <NAME>. Languages without their own account
post to the shared one, but only if they are listed for that platform in
config "shared_account_languages" (a platform missing there means every
language may use the shared account).

usage: python3 publish/accounts.py check <lang> <platform>
           exit 0 if the language has an account to post to, 1 if not
       python3 publish/accounts.py run <lang> <platform> -- <command>...
           runs the command with that account's variables set
       python3 publish/accounts.py which <lang> <platform>
           prints "own", "shared" or "none"
env:   SECRETS_JSON (the workflow's toJSON(secrets)); falls back to the
       process environment for local runs.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "..", "generator", "config.json"), encoding="utf-8"))

# "account" variables identify one account and must all come from the same
# place; "common" ones (the YouTube OAuth client) may be shared across accounts.
PLATFORMS = {
    "youtube": {"account": ["YT_REFRESH_TOKEN"], "common": ["YT_CLIENT_ID", "YT_CLIENT_SECRET"]},
    "instagram": {"account": ["IG_USER_ID", "IG_ACCESS_TOKEN"], "common": []},
    "facebook": {"account": ["FB_PAGE_ID", "FB_PAGE_TOKEN"], "common": []},
    "threads": {"account": ["THREADS_USER_ID", "THREADS_TOKEN"], "common": []},
}


def secrets():
    raw = os.environ.get("SECRETS_JSON")
    values = json.loads(raw) if raw else dict(os.environ)
    return {k: v for k, v in values.items() if v}


def resolve(lang, platform):
    """Returns ("own" | "shared" | "none", {variable: value})."""
    spec = PLATFORMS[platform]
    values = secrets()
    suffix = "_" + lang.upper()
    own = [n for n in spec["account"] if n + suffix in values]
    if own and len(own) < len(spec["account"]):
        missing = [n + suffix for n in spec["account"] if n not in own]
        sys.exit(f"{lang} {platform}: has {own[0]}{suffix} but not {', '.join(missing)}")

    if own:
        kind, env = "own", {n: values[n + suffix] for n in spec["account"]}
    else:
        allowed = CONFIG.get("shared_account_languages", {}).get(platform)
        if (allowed is not None and lang not in allowed) or \
                not all(n in values for n in spec["account"]):
            return "none", {}
        kind, env = "shared", {n: values[n] for n in spec["account"]}
    for n in spec["common"]:
        if n + suffix in values or n in values:
            env[n] = values.get(n + suffix, values.get(n))
    return kind, env


def main():
    cmd, lang, platform = sys.argv[1:4]
    kind, env = resolve(lang, platform)
    if cmd == "which":
        print(kind)
    elif cmd == "check":
        sys.exit(0 if kind != "none" else 1)
    elif cmd == "run":
        if kind == "none":
            sys.exit(f"{lang} has no {platform} account")
        command = sys.argv[sys.argv.index("--") + 1:]
        os.environ.pop("SECRETS_JSON", None)  # the command only needs its own account
        os.environ.update(env)
        os.execvp(command[0], command)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
