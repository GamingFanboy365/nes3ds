#!/usr/bin/env bash
#
# Attaches devkitARM's GDB to Azahar's GDB stub, with virtuanes_3ds.elf
# for symbols. Start the emulator first with: tools/azahar/run.sh -g ...
#
#   tools/azahar/gdb.sh [PORT] [GDB ARGS...]
#
set -euo pipefail

PORT=24689
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then PORT="$1"; shift; fi

IMAGE="${DEVKITARM_IMAGE:-devkitpro/devkitarm:20260610}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

exec docker run --rm -it --network host \
    -v "$ROOT:/src" -w /src \
    "$IMAGE" \
    /opt/devkitpro/devkitARM/bin/arm-none-eabi-gdb virtuanes_3ds.elf \
        -ex "target remote 127.0.0.1:$PORT" "$@"
