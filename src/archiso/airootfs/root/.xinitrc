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

# Set LXQt environment variables
export XDG_CURRENT_DESKTOP=LXQt
export QT_QPA_PLATFORMTHEME=lxqt

# If a specific app was requested, run it with openbox
if [ -n "$1" ]; then
    openbox &
    exec "$@"
else
    # Default: start LXQt desktop environment
    exec startlxqt
fi