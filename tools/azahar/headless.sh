#!/usr/bin/env bash
#
# Runs inside the linuxserver/azahar container; started by run.sh.
#
#   headless.sh TIMEOUT "AZAHAR ARGS" [STEP...]
#
set -uo pipefail

TIMEOUT="$1"
AZAHAR_ARGS="$2"
shift 2

# Azahar's default keyboard mapping for the 3DS buttons.
declare -A KEYS=(
    [a]=a [b]=s [x]=z [y]=x [l]=q [r]=w [start]=m [select]=n
    [up]=t [down]=g [left]=f [right]=h
)

FB=/tmp/fb
LOG=/config/.local/share/azahar-emu/log/azahar_log.txt
mkdir -p "$FB"

# With single window mode off, Azahar shows the 3DS screens in their own
# 400x480 window (top screen above bottom screen, at 1x), which is what
# gets screenshotted.
CONF=/config/.config/azahar-emu/qt-config.ini
sed -i '/^singleWindowMode=/d; /^singleWindowMode\\default=/d; s/^\[UI\]$/[UI]\nsingleWindowMode=false/' "$CONF"

Xvfb :99 -screen 0 1280x720x24 -fbdir "$FB" -nolisten tcp >/dev/null 2>&1 &
export DISPLAY=:99 QT_QPA_PLATFORM=xcb
for _ in $(seq 50); do
    [ -e /tmp/.X11-unix/X99 ] && break
    sleep 0.1
done

# shellcheck disable=SC2086
azahar $AZAHAR_ARGS /app.3dsx >/tmp/azahar_stdout.txt 2>&1 &
AZ=$!

finish() {
    kill "$AZ" 2>/dev/null
    for _ in $(seq 50); do
        kill -0 "$AZ" 2>/dev/null || break
        sleep 0.1
    done
    kill -9 "$AZ" 2>/dev/null
    cp "$LOG" /out/azahar_log.txt 2>/dev/null
    echo "log: azahar_log.txt"
}
trap finish EXIT
# This script is PID 1 in the container, which ignores an untrapped SIGTERM.
trap 'exit 124' TERM INT

( sleep "$TIMEOUT"; echo "timeout after ${TIMEOUT}s"; kill $$ ) &
WATCHDOG=$!

# Top-level Azahar windows: the main window is titled "Azahar <version>",
# the render window "Azahar". The render window only appears once the app
# has booted, which can take a while with software OpenGL, or until a
# debugger attaches with -g.
azahar_windows() {
    xdotool search --maxdepth 1 --onlyvisible --class Azahar 2>/dev/null
}
WIN=""
MAIN=""
for _ in $(seq $((TIMEOUT * 5))); do
    for w in $(azahar_windows); do
        if [ "$(xdotool getwindowname "$w")" = Azahar ]; then WIN=$w; else MAIN=$w; fi
    done
    [ -n "$WIN" ] && break
    sleep 0.2
done
if [ -z "$WIN" ]; then
    echo "Azahar did not open its render window. Windows:" >&2
    for w in $(xdotool search --name ''); do
        echo "  $w '$(xdotool getwindowname "$w")'" >&2
    done
    cat /tmp/azahar_stdout.txt >&2
    exit 1
fi
[ -n "$MAIN" ] && xdotool windowmove "$MAIN" 420 0
xdotool windowmove "$WIN" 0 0 windowsize "$WIN" 400 480 windowfocus --sync "$WIN" 2>/dev/null

shot() {
    if xwdtopnm "$FB/Xvfb_screen0" 2>/dev/null | pamcut 0 0 400 480 | pnmtopng -force >"/out/$1.png" 2>/dev/null; then
        echo "shot: $1.png"
    else
        echo "shot: $1.png failed" >&2
    fi
}

for step in "$@"; do
    IFS=: read -r cmd arg ms <<<"$step"
    if [[ "$cmd" =~ ^(key|down|up)$ ]]; then
        k="${KEYS[$arg]:-}"
        if [ -z "$k" ]; then
            echo "unknown button: $arg" >&2
            continue
        fi
    fi
    case "$cmd" in
        wait)
            # In the background, so that the timeout can interrupt it.
            sleep "$arg" &
            wait $! ;;
        key)
            xdotool windowfocus "$WIN" keydown "$k"
            sleep "$(awk "BEGIN { print ${ms:-150} / 1000 }")"
            xdotool keyup "$k" ;;
        down)
            xdotool windowfocus "$WIN" keydown "$k" ;;
        up)
            xdotool keyup "$k" ;;
        shot)
            shot "$arg" ;;
        *)
            echo "unknown step: $step" >&2 ;;
    esac
    if ! kill -0 "$AZ" 2>/dev/null; then
        echo "Azahar exited" >&2
        break
    fi
done

# No steps: just run (e.g. while a debugger is attached) until the
# emulator exits or the timeout hits.
if [ $# -eq 0 ]; then
    wait "$AZ"
fi
kill "$WATCHDOG" 2>/dev/null
