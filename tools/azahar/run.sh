#!/usr/bin/env bash
#
# Runs virtuanes_3ds.3dsx in the Azahar 3DS emulator, inside Docker
# (linuxserver/azahar image), for debugging without real hardware.
#
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: tools/azahar/run.sh [options] [-- STEP...]

Runs virtuanes_3ds.3dsx in the Azahar 3DS emulator inside Docker.

Options:
  -r, --rom FILE      put FILE on the emulated SD card (repeatable). The SD card
                      is emptied of NES/FDS/NSF files first, so with a single ROM
                      "key:a" at the ROM menu loads it.
  -a, --app FILE      .3dsx to run (default: virtuanes_3ds.3dsx)
  -o, --out DIR       where screenshots and the log go (default: .azahar/out)
  -g, --gdb [PORT]    start Azahar's GDB stub on 127.0.0.1:PORT (default 24689);
                      the app waits for the debugger before it starts
      --gui           show the emulator on your X11 display instead of Xvfb
  -t, --timeout SEC   stop the emulator after SEC seconds (headless, default 120)
  -h, --help

Steps run in order once the emulator window is up (headless mode only):
  wait:SEC            sleep SEC seconds (fractions allowed)
  key:BUTTON[:MS]     hold a 3DS button for MS milliseconds (default 150)
                      BUTTON: a b x y l r start select up down left right
  down:BUTTON         press a button and keep it held...
  up:BUTTON           ...until this step releases it
  shot:NAME           save the screen to OUT/NAME.png (top screen above bottom)

The Azahar log, including DEBUGOUT() output from a `make DEBUGOUT=1`
build, is always copied to OUT/azahar_log.txt at the end.

Example:
  tools/azahar/run.sh -r game.nes -- wait:8 key:a wait:5 shot:title \
      key:start wait:3 shot:ingame
EOF
}

IMAGE="${AZAHAR_IMAGE:-linuxserver/azahar:latest}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$ROOT/.azahar"

APP="$ROOT/virtuanes_3ds.3dsx"
OUT="$WORK/out"
ROMS=()
GDB_PORT=""
GUI=0
TIMEOUT=120
STEPS=()

while [ $# -gt 0 ]; do
    case "$1" in
        -r|--rom)     ROMS+=("$2"); shift 2 ;;
        -a|--app)     APP="$2"; shift 2 ;;
        -o|--out)     OUT="$2"; shift 2 ;;
        -g|--gdb)
            if [[ "${2:-}" =~ ^[0-9]+$ ]]; then GDB_PORT="$2"; shift 2
            else GDB_PORT=24689; shift; fi ;;
        --gui)        GUI=1; shift ;;
        -t|--timeout) TIMEOUT="$2"; shift 2 ;;
        -h|--help)    usage; exit 0 ;;
        --)           shift; STEPS=("$@"); break ;;
        *)            echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [ ! -f "$APP" ]; then
    echo "$APP not found; build it first with tools/build.sh" >&2
    exit 1
fi

# Emulator profiles (config, NAND, SD card): headless runs start from
# tools/azahar/qt-config.ini every time; the --gui profile keeps whatever
# you change in Azahar's settings.
if [ "$GUI" = 1 ]; then HOMEDIR="$WORK/gui"; else HOMEDIR="$WORK/headless"; fi
CONFDIR="$HOMEDIR/.config/azahar-emu"
SDMC="$HOMEDIR/.local/share/azahar-emu/sdmc"
mkdir -p "$CONFDIR" "$SDMC" "$OUT"
OUT="$(cd "$OUT" && pwd)"

CONF="$CONFDIR/qt-config.ini"
if [ "$GUI" = 0 ] || [ ! -f "$CONF" ]; then
    cp "$ROOT/tools/azahar/qt-config.ini" "$CONF"
fi

find "$SDMC" -maxdepth 1 -type f \( -iname '*.nes' -o -iname '*.fds' -o -iname '*.nsf' \) -delete
for rom in ${ROMS[@]+"${ROMS[@]}"}; do
    cp "$rom" "$SDMC/"
done
cp "$APP" "$WORK/app.3dsx"

DOCKER_ARGS=(--rm -i
    -u "$(id -u):$(id -g)"
    -e HOME=/config
    -v "$HOMEDIR:/config"
    -v "$WORK/app.3dsx:/app.3dsx:ro"
    -v "$OUT:/out"
    -v "$ROOT/tools/azahar/headless.sh:/headless.sh:ro"
    --entrypoint bash)
AZAHAR_ARGS=()
if [ -n "$GDB_PORT" ]; then
    # (--gui uses the host network, where the port is reachable anyway.)
    [ "$GUI" = 1 ] || DOCKER_ARGS+=(-p "127.0.0.1:$GDB_PORT:$GDB_PORT")
    AZAHAR_ARGS+=(-g "$GDB_PORT")
    echo "GDB stub on 127.0.0.1:$GDB_PORT (tools/azahar/gdb.sh connects to it)"
fi

if [ "$GUI" = 1 ]; then
    # The host network keeps the hostname in the X authority cookie valid.
    DOCKER_ARGS+=(--network host
        -e DISPLAY="${DISPLAY:?--gui needs an X11 DISPLAY}"
        -v /tmp/.X11-unix:/tmp/.X11-unix)
    if [ -n "${XAUTHORITY:-}" ] && [ -f "$XAUTHORITY" ]; then
        DOCKER_ARGS+=(-e XAUTHORITY=/tmp/.Xauthority -v "$XAUTHORITY:/tmp/.Xauthority:ro")
    elif [ -f "$HOME/.Xauthority" ]; then
        DOCKER_ARGS+=(-e XAUTHORITY=/tmp/.Xauthority -v "$HOME/.Xauthority:/tmp/.Xauthority:ro")
    fi
    exec docker run "${DOCKER_ARGS[@]}" \
        "$IMAGE" -c 'exec azahar "$@" /app.3dsx' azahar ${AZAHAR_ARGS[@]+"${AZAHAR_ARGS[@]}"}
fi

docker run "${DOCKER_ARGS[@]}" "$IMAGE" /headless.sh "$TIMEOUT" \
    "${AZAHAR_ARGS[*]:-}" ${STEPS[@]+"${STEPS[@]}"}
