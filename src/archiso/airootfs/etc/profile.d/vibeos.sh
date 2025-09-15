#!/bin/bash
# VibeOS Environment Setup
# Sets up environment variables and paths for VibeOS

# Add VibeOS to Python path
export PYTHONPATH="/usr/lib/vibeos:$PYTHONPATH"

# Set VibeOS version
export VIBEOS_VERSION="0.1.0-alpha"

# Enable color output
export TERM=xterm-256color

# Set default editor
export EDITOR=vim

# Aliases for quick access
alias vibe='vibesh'
alias vibehelp='vibesh --help'

# Function to quickly switch to vibesh
vibeos() {
    exec /usr/local/bin/vibesh
}

# AI Assistant commands
alias claude='claude-code'
alias ai='vibeos-ai-selector'

# Display message on non-TTY1 terminals
if [[ "$(tty)" != "/dev/tty1" ]]; then
    echo "========================================"
    echo "  VibeOS Debug Terminal"
    echo "========================================"
    echo ""
    echo "You're in a debug bash shell."
    echo "Type 'vibeos' to launch the natural language shell."
    echo "Type 'ai' to select AI assistant (Claude Code)."
    echo "TTY1 runs AI selector by default."
    echo ""
fi