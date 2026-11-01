#!/usr/bin/env bash
# Makes the promo voiceovers on a Mac and uploads them to R2. Uses the Parler
# environment of the app repo's voice scripts (~/venvs/parler) and the R2 keys
# from the environment or the macOS Keychain (service "gita-r2"), as there.
#   promo/run_voiceovers_mac.sh            # all languages and videos
#   LANGS="ml hi" promo/run_voiceovers_mac.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/venvs/parler/bin/python"
[ -x "$PY" ] || { echo "No ~/venvs/parler: run the app repo's scripts/run_voice_session_mac.sh once first."; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing: brew install ffmpeg"; exit 1; }
"$PY" -m pip install -q boto3
for key in R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY; do
  value="${!key:-}"
  [ -z "$value" ] && value="$(security find-generic-password -s gita-r2 -a "$key" -w 2>/dev/null || true)"
  [ -n "$value" ] || { echo "No $key (export it or store it in the Keychain as for the voice scripts)"; exit 1; }
  export "$key=$value"
done
args=(--upload)
[ -n "${LANGS:-}" ] && args+=(--langs $LANGS)
caffeinate -i "$PY" promo/make_voiceovers.py "${args[@]}"
