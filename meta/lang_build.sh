#!/usr/bin/env bash

set -eu
cd "$(dirname "$0")/.."

# languages already generated (by whichever hook ran first) -- skip;
# remove checker/res/languages to force a rebuild
if [[ -d checker/res/languages ]]; then
    exit 0
fi

# Set LANGTOOL_IMAGE to pull a pre-built image (e.g. from a registry in CI).
# Without it, the image is always built from service/language-tool sources.
if [[ -v LANGTOOL_IMAGE ]]; then
    IMAGE="$LANGTOOL_IMAGE"
    docker pull "$IMAGE"
else
    IMAGE="language-tool-builder"
    docker build -t "$IMAGE" --target builder service/language-tool
fi

mkdir -p checker/res/languages checker/res/languages-additional
docker run --rm \
    -v "$(pwd)/checker/res/languages:/app/languages" \
    -v "$(pwd)/checker/res/languages-additional:/app/languages-additional" \
    --entrypoint '/bin/bash' "$IMAGE" -c 'make langs'
