#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."

# Cleanup hints
if [[ $# -eq 0 ]] ; then
  rm -f service/spellchecker/*_test.go
fi

# Build language static files (shared with checker_build.sh, skipped if present)
meta/lang_build.sh
if [[ ! -d service/language-tool/languages ]]; then
    cp -ra checker/res/languages service/language-tool/languages
fi

# Build frontend (already gone when a previous run cleaned it up)
if [[ -d service/frontend ]]; then
    docker run --rm -v $(pwd)'/service/frontend:/src' --entrypoint '/bin/bash' node:26 -c 'cd /src && npm install && npm run build'
    rm -rf service/gateway/static
    cp -ra service/frontend/dist/frontend/browser service/gateway/static

    # Remove frontend sources
    if [[ $# -eq 0 ]] ; then
      rm -rf service/frontend
    else
      echo "Skipped cleanup"
      exit 1  # so we find it if this happens in CI
    fi
fi
