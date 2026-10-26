#!/usr/bin/env bash

set -e

cleanup_directory() {
  find "$1" -mindepth 1 -maxdepth 1 -type d -mmin +45 | grep -v '/00000000-' | xargs -r rm -rf
}

while true; do
  echo "running cleanup ..."
  cleanup_directory /data/files
  echo "done."
  sleep 300 || exit 0
done

