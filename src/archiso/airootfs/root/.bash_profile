#!/bin/bash
# VibeOS root user profile
# Launches vibesh on first TTY, regular bash on others

if [[ "$(tty)" == "/dev/tty1" ]]; then
    # Launch VibeOS natural language shell on TTY1
    exec /usr/local/bin/vibesh
else
    # Regular bash on other TTYs for debugging
    [[ -f ~/.bashrc ]] && . ~/.bashrc
fi