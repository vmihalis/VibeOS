#!/bin/sh
# VibeOS X11 initialization
# Minimal configuration for running GUI apps when needed

# Set up basic X environment
if [ -d /etc/X11/xinit/xinitrc.d ]; then
    for f in /etc/X11/xinit/xinitrc.d/?*.sh; do
        [ -x "$f" ] && . "$f"
    done
    unset f
fi

# Start dbus for Firefox
if which dbus-launch >/dev/null && test -z "$DBUS_SESSION_BUS_ADDRESS"; then
    eval "$(dbus-launch --sh-syntax --exit-with-session)"
fi

# If a specific app was requested, run it
if [ -n "$1" ]; then
    exec "$@"
else
    # Default: start openbox with xterm
    exec openbox-session
fi