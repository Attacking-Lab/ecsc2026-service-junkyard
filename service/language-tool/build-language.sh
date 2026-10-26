#!/usr/bin/env bash

set -eu

mkdir -p tmp
mkdir -p languages
mkdir -p languages-additional

if [ ! -f "tmp/$1.tar.gz" ]; then
  wget "$2" -O"tmp/$1.tar.gz" || (rm -f "tmp/$1.tar.gz" ; exit 1)
fi

# create wordlist
tar -xf "tmp/$1.tar.gz" --wildcards '*-words.txt' --to-stdout | sed -r 's/.*?\t(.{2,})\t.*/\1/' > "languages/$1.txt"

# collect sentences
tar -xf "tmp/$1.tar.gz" --wildcards '*-sentences.txt' --to-stdout | sed -r 's/.*?\t(.*)/\1/' > "languages-additional/$1-sentences.txt"

export LANG_DIR=./languages
./language-tool --mode generate -f "languages-additional/$1-sentences.txt" --language "$1"

echo DONE
