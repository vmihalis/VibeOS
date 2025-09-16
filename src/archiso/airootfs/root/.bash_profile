#!/bin/bash
# VibeOS root user profile
# Launches vibesh on first TTY, regular bash on others

if [[ "$(tty)" == "/dev/tty1" ]]; then
    # Clear screen and show VibeOS boot message
    clear
    echo "========================================================"
    echo "    Welcome to VibeOS v0.2.0 - AI-Powered OS"
    echo "========================================================"
    echo ""
    echo "This operating system runs entirely on AI."
    echo "All commands are processed through Claude Code."
    echo ""

    # Check critical dependencies
    if ! command -v python3 &> /dev/null; then
        echo "❌ CRITICAL: Python3 not found. System cannot start."
        echo "Falling back to bash."
        [[ -f ~/.bashrc ]] && . ~/.bashrc
        exit 0
    fi

    # Check debug mode
    VIBEOS_DEBUG="${VIBEOS_DEBUG:-true}"
    if [ "$VIBEOS_DEBUG" = "true" ]; then
        echo "[DEBUG MODE ENABLED]"
        echo ""
    fi

    # Check network connectivity
    echo "Checking network connectivity..."
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        echo "✅ Network is connected"
    else
        echo "⚠️  No network connectivity detected"
        echo "Attempting to establish network connection..."

        # Try to run network setup
        if [ -x /usr/local/bin/vibeos-network-setup ]; then
            /usr/local/bin/vibeos-network-setup
        else
            echo "Network setup script not found, trying manual setup..."
            # Simple fallback
            for interface in $(ip link show | grep -E "^[0-9]+:" | cut -d: -f2 | tr -d ' ' | grep -v "^lo$"); do
                ip link set "$interface" up 2>/dev/null || true
                dhcpcd -n "$interface" 2>/dev/null &
            done
            sleep 3
        fi

        # Check again
        if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
            echo "✅ Network connectivity established!"
        else
            echo "❌ Still no network. Claude Code will not be able to connect."
            echo "Try running: vibeos-debug network"
        fi
    fi
    echo ""

    # Check Claude Code status
    echo "Checking Claude Code status..."

    if [ "$VIBEOS_DEBUG" = "true" ]; then
        echo "[DEBUG] Checking installation methods:"
        echo -n "[DEBUG]   /usr/bin/claude-code exists: "
        [ -f /usr/bin/claude-code ] && echo "YES" || echo "NO"

        echo -n "[DEBUG]   /usr/bin/claude-code executable: "
        [ -x /usr/bin/claude-code ] && echo "YES" || echo "NO"

        echo -n "[DEBUG]   Node module exists: "
        [ -d /usr/lib/node_modules/@anthropic-ai/claude-code ] && echo "YES" || echo "NO"

        echo -n "[DEBUG]   'which claude-code' returns: "
        which claude-code 2>/dev/null || echo "NOT FOUND"

        echo -n "[DEBUG]   Direct test of wrapper: "
        if /usr/bin/claude-code --version &>/dev/null; then
            echo "WORKS"
        else
            echo "FAILS (exit code: $?)"
        fi
        echo ""
    fi

    if command -v claude-code &> /dev/null; then
        echo "✅ Claude Code is installed"
        echo ""
        echo "If not authenticated, run: claude-code auth"
    else
        echo "❌ CRITICAL: Claude Code NOT INSTALLED"
        echo ""
        echo "VibeOS CANNOT function without Claude Code!"
        echo "Install immediately with:"
        echo "  npm install -g @anthropic-ai/claude-code"
        echo "  claude-code auth"

        if [ "$VIBEOS_DEBUG" = "true" ]; then
            echo ""
            echo "[DEBUG] Additional diagnostics:"
            echo "[DEBUG] PATH=$PATH"
            echo "[DEBUG] Node version: $(node --version 2>/dev/null || echo 'Node not found')"
            echo "[DEBUG] NPM version: $(npm --version 2>/dev/null || echo 'NPM not found')"
            echo "[DEBUG] Looking for claude-code files:"
            find /usr -name "*claude*" -type f 2>/dev/null | head -10
        fi
    fi

    echo ""
    echo "GUI Support:"
    echo "  • Firefox browser installed for authentication"
    echo "  • Run 'vibeos-browser' to launch browser"
    echo "  • Or say 'authenticate claude code' in vibesh"
    echo ""
    echo "========================================================"
    echo ""

    # Launch VibeOS natural language shell on TTY1
    if [[ -f /usr/local/bin/vibesh ]]; then
        echo "Starting VibeOS AI-Powered Shell..."
        python3 /usr/local/bin/vibesh 2>&1
        # If vibesh exits, fall back to bash
        echo "vibesh exited. Falling back to bash."
        [[ -f ~/.bashrc ]] && . ~/.bashrc
    else
        echo "❌ CRITICAL: vibesh not found at /usr/local/bin/vibesh"
        echo "System files corrupted. Falling back to bash."
        [[ -f ~/.bashrc ]] && . ~/.bashrc
    fi
else
    # Regular bash on other TTYs for debugging
    [[ -f ~/.bashrc ]] && . ~/.bashrc
fi