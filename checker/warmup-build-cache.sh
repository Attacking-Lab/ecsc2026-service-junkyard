#!/usr/bin/env bash

set -e

docker build --target base -t junkyard-buildcache-tmp .
echo DONE
