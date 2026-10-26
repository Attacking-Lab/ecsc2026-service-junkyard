#!/usr/bin/env bash
# Builds libspellchecker.so and the precomputed dictionary index (dictionaries.idx) next to __init__.py,
# same as the Dockerfile does. Usage: spellchecker/build.sh [language dir]
set -euo pipefail
cd "$(dirname "$0")"

GO="$(command -v go || { echo 'error: go not found in PATH' >&2; exit 1; })"
LANG_DIR="${1:-../res/languages}"

"$GO" build -buildmode=c-shared -o libspellchecker.so .
"$GO" run . build-index "$LANG_DIR" dictionaries.idx
