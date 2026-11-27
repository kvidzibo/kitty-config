#!/bin/bash
# Open a folder in a named tab of the Kitty instance on this display.
set -eu

cd -- "${1:-$PWD}"
folder=$PWD
title=$(basename -- "$folder")

open_tab() {
  local address=$1 window_id
  window_id=$(kitty @ --to "$address" launch --type=tab \
    --cwd="$folder") || return 1
  # Set separately: launch treats the literal folder name "current" specially.
  kitty @ --to "$address" set-tab-title --match="window_id:$window_id" -- "$title" || true
  # Activating a tab alone does not raise Kitty above the file manager.
  kitty @ --to "$address" focus-window --match="id:$window_id" || true
}

# An explicit address must never fall through to a different instance.
if [ -n "${KITTY_LISTEN_ON:-}" ]; then
  open_tab "$KITTY_LISTEN_ON"
  exit
fi

# Thunar's launch context may spell :0 as :0.0 (the default X11 screen).
display=${DISPLAY:-}
display=${display%.0}
# Match the socket convention in kitty.conf and persist_kitty_session.
for pid in $(pgrep -u "$(id -u)" -x kitty || true); do
  # Do not open tabs on another X11 desktop (including isolated UI tests).
  if [ -n "$display" ] && \
    grep -zqxF -e "DISPLAY=$display" -e "DISPLAY=$display.0" \
      "/proc/$pid/environ" 2>/dev/null; then
    if open_tab "unix:@mykitty-$pid"; then
      exit
    fi
  fi
done

# With no reachable Kitty, start one shell, not the saved session layout.
kitty --session=none --directory="$folder" --title="$title" </dev/null >/dev/null 2>&1 &
pid=$!
for ((attempt=0; attempt<50; attempt++)); do
  if kitty @ --to "unix:@mykitty-$pid" set-tab-title -- "$title" 2>/dev/null; then
    exit
  fi
  kill -0 "$pid" 2>/dev/null || break
  sleep 0.1
done
printf 'Could not set the Kitty tab title; check remote control configuration.\n' >&2
exit 1
