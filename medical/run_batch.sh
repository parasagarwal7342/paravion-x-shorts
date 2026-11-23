#!/usr/bin/env bash
# Build every episode folder given (or all of them).
cd "$(dirname "$0")"
for ep in "${@:-episodes/*/}"; do ./make_episode.sh "${ep%/}" || echo "FAILED: $ep"; done
