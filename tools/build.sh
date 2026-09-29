#!/usr/bin/env bash
#
# Builds virtuanes_3ds.3dsx (and .cia) with devkitARM from the official
# devkitpro/devkitarm Docker image, so no local devkitPro install is needed.
#
#   tools/build.sh              # same as `make`
#   tools/build.sh DEBUGOUT=1   # route VirtuaNES DEBUGOUT() to the emulator log
#   tools/build.sh clean
#
# Any arguments are passed straight to make.
#
set -euo pipefail

IMAGE="${DEVKITARM_IMAGE:-devkitpro/devkitarm:20260610}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

exec docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "$ROOT:/src" -w /src \
    "$IMAGE" \
    make -j"$(nproc)" "$@"
