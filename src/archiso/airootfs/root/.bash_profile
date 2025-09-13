#!/bin/bash
# VibeOS root user profile
# Launches vibesh on first TTY, regular bash on others

if [[ "$(tty)" == "/dev/tty1" ]]; then
    # MOTD is already displayed by the system, no need to show it again
    
    # Check Python is available
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python3 not found. Cannot launch vibesh."
        echo "Falling back to bash."
        [[ -f ~/.bashrc ]] && . ~/.bashrc
        exit 0
    fi
    
    # Launch VibeOS natural language shell on TTY1
    if [[ -f /usr/local/bin/vibesh ]]; then
        # Try to run vibesh even if not marked executable
        echo "Starting VibeOS Natural Language Shell..."
        python3 /usr/local/bin/vibesh 2>&1
        # If vibesh fails, fall back to bash
        echo "vibesh exited. Falling back to bash."
        [[ -f ~/.bashrc ]] && . ~/.bashrc
    else
        echo "Warning: vibesh not found at /usr/local/bin/vibesh"
        echo "Falling back to bash."
        [[ -f ~/.bashrc ]] && . ~/.bashrc
    fi
else
    # Regular bash on other TTYs for debugging
    [[ -f ~/.bashrc ]] && . ~/.bashrc
fi