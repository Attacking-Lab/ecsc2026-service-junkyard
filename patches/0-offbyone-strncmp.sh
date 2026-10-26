#!/bin/sh
# Runs with the working directory set to the copy of service/.

set -e

patch -p2 -i "$(dirname "$0")/patch-0-offbyone-strncmp.diff"
