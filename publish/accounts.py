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
       python3 publish/accounts.py env-yaml
           prints the workflow env block listing every account secret
env:   the account secrets (shared and per language) as environment variables.
       Workflows must list them by name (see env-yaml): GitHub holds runs that
       pass toJSON(secrets) in a public repo for approval.
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
    return {k: v for k, v in os.environ.items() if v}


def secret_names():
    """Every shared and per-language account secret, in workflow order."""
    names = []
    for spec in PLATFORMS.values():
        for n in spec["account"] + spec["common"]:
            names.append(n)
        for code in CONFIG["languages"]:
            names += [f"{n}_{code.upper()}" for n in spec["account"]]
    return names


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
    if sys.argv[1:2] == ["env-yaml"]:
        for n in secret_names():
            print(f"{n}: ${{{{ secrets.{n} }}}}")
        return
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
        for n in secret_names():  # the command only gets its own account
            os.environ.pop(n, None)
        os.environ.update(env)
        os.execvp(command[0], command)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
