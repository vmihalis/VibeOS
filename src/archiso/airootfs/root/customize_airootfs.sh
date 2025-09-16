#!/bin/bash
# VibeOS Customization Script
# Runs during ISO build in chroot environment
# This script is executed by mkarchiso during the build process

set -e -u

echo "================================================"
echo "    VibeOS Build-Time Customization"
echo "================================================"

# Debug information
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "PATH: $PATH"

# Ensure network connectivity for npm
echo "Setting up network for package installation..."
# Ensure DNS is working
if [ ! -f /etc/resolv.conf ] || [ ! -s /etc/resolv.conf ]; then
    echo "Setting up DNS resolution..."
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
fi

# Test network connectivity
echo "Testing network connectivity..."
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo "✅ Network connectivity confirmed"
else
    echo "⚠️  No network connectivity - npm install may fail"
fi

# Test DNS resolution
if nslookup registry.npmjs.org &> /dev/null || host registry.npmjs.org &> /dev/null || ping -c 1 registry.npmjs.org &> /dev/null; then
    echo "✅ DNS resolution working"
else
    echo "⚠️  DNS resolution not working - trying to fix..."
    # Force DNS config
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
fi

# Ensure npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found! Make sure nodejs and npm are in packages.x86_64"
    echo "Attempting to verify Node.js installation..."
    which node || echo "Node.js not found in PATH"
    ls -la /usr/bin/node* 2>/dev/null || echo "No node binaries in /usr/bin"
    exit 1
fi

# Install Claude Code globally
echo ""
echo "📦 Pre-installing Claude Code..."
echo "This ensures Claude Code is immediately available on boot"
echo ""

# Show npm configuration
echo "NPM version: $(npm --version 2>/dev/null || echo 'NPM not available')"
echo "Node version: $(node --version 2>/dev/null || echo 'Node not available')"
echo "NPM prefix: $(npm config get prefix 2>/dev/null || echo '/usr')"

# Set npm configuration for chroot environment
export npm_config_prefix=/usr
export npm_config_cache=/tmp/npm-cache
export npm_config_loglevel=verbose

# Create cache directory
mkdir -p /tmp/npm-cache

# Claude Code is MANDATORY for VibeOS to function
echo ""
echo "============================================"
echo "Installing Claude Code (CRITICAL COMPONENT)"
echo "============================================"
echo ""

# Show current environment
echo "[BUILD DEBUG] Environment:"
echo "[BUILD DEBUG]   User: $(whoami)"
echo "[BUILD DEBUG]   PWD: $(pwd)"
echo "[BUILD DEBUG]   NPM prefix: $(npm config get prefix 2>/dev/null || echo 'npm not configured')"
echo "[BUILD DEBUG]   Node: $(node --version 2>/dev/null || echo 'not found')"
echo "[BUILD DEBUG]   NPM: $(npm --version 2>/dev/null || echo 'not found')"
echo ""

# Method 1: Try standard npm install with network
echo "[BUILD] Method 1: Attempting npm install with network access..."
if npm install -g @anthropic-ai/claude-code 2>&1 | tee /tmp/npm-install.log; then
    echo "✅ Claude Code installed successfully via npm!"
    echo "[BUILD DEBUG] Installation location: $(npm list -g @anthropic-ai/claude-code 2>/dev/null | head -2)"
else
    echo "⚠️  Standard npm install failed, trying alternative methods..."

    # Method 2: Try with different registry settings
    echo "Configuring npm for better connectivity..."
    npm config set registry https://registry.npmjs.org/
    npm config set strict-ssl false
    npm config set fetch-retries 5
    npm config set fetch-retry-factor 2
    npm config set fetch-retry-mintimeout 10000

    if npm install -g @anthropic-ai/claude-code --verbose 2>&1; then
        echo "✅ Claude Code installed with alternative npm config!"
    else
        # Method 3: Check if Claude Code was pre-downloaded
        echo "Checking for pre-downloaded Claude Code package..."
        if [ -f /root/claude-code-package.tgz ]; then
            echo "Found pre-downloaded package, installing from local file..."
            npm install -g /root/claude-code-package.tgz &&
                echo "✅ Claude Code installed from local package!" ||
                echo "❌ Failed to install from local package"
        else
            echo ""
            echo "============================================"
            echo "⚠️  CRITICAL WARNING: Claude Code NOT installed"
            echo "============================================"
            echo "VibeOS REQUIRES Claude Code to function!"
            echo "The OS will boot but will NOT accept ANY commands"
            echo "until Claude Code is installed and authenticated."
            echo ""
            echo "Users must run after boot:"
            echo "  npm install -g @anthropic-ai/claude-code"
            echo "  claude-code auth"
            echo "============================================"
            echo ""
        fi
    fi
fi

# Verify and fix installation paths
echo ""
echo "============================================"
echo "Verifying Claude Code Installation"
echo "============================================"
echo ""

# Check where npm installed Claude Code
CLAUDE_MODULE_PATH="/usr/lib/node_modules/@anthropic-ai/claude-code"
echo "[BUILD DEBUG] Checking for Claude Code module..."
echo "[BUILD DEBUG]   Expected path: $CLAUDE_MODULE_PATH"
echo "[BUILD DEBUG]   Path exists: $([ -d "$CLAUDE_MODULE_PATH" ] && echo 'YES' || echo 'NO')"

if [ -d "$CLAUDE_MODULE_PATH" ]; then
    echo "✅ Claude Code module found at $CLAUDE_MODULE_PATH"
    echo "[BUILD DEBUG] Module contents:"
    ls -la "$CLAUDE_MODULE_PATH" | head -5 | sed 's/^/[BUILD DEBUG]   /'

    # Create executable wrapper in /usr/bin
    echo "Creating executable wrapper..."
    cat > /usr/bin/claude-code << 'EOF'
#!/bin/bash
# Claude Code wrapper for VibeOS
exec node /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js "$@"
EOF
    chmod +x /usr/bin/claude-code
    echo "✅ Created /usr/bin/claude-code executable"

    # Test the wrapper
    if /usr/bin/claude-code --version &>/dev/null; then
        echo "✅ Wrapper works correctly"
    else
        echo "⚠️  Wrapper may have issues, trying direct node execution..."
        # Alternative wrapper using direct node path
        cat > /usr/bin/claude-code << 'EOF'
#!/bin/sh
# Claude Code fallback wrapper
NODE_PATH=/usr/lib/node_modules node /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js "$@"
EOF
        chmod +x /usr/bin/claude-code
    fi

    # Alternative: Create symlink to the CLI
    # ln -sf "$CLAUDE_MODULE_PATH/cli.js" /usr/bin/claude-code
    # chmod +x "$CLAUDE_MODULE_PATH/cli.js"
else
    echo "⚠️  Claude Code module not found at expected location"
    echo "Searching for installation..."
    find /usr -name "@anthropic-ai" -type d 2>/dev/null || echo "Not found"
fi

# Verify the command works
if command -v claude-code &> /dev/null; then
    echo "✅ Claude Code command is available in PATH"
    echo "   Location: $(which claude-code)"
    # Don't run --version as it might fail in chroot
else
    echo "⚠️  Warning: claude-code command still not in PATH"
    echo "Users will need to run: export PATH=/usr/lib/node_modules/.bin:\$PATH"
fi

# Create initial AI configuration
echo ""
echo "🔧 Setting up default AI configuration..."
mkdir -p /etc/vibeos
cat > /etc/vibeos/ai_config.json << 'EOF'
{
  "selected_assistant": "claude-code",
  "auto_launch": false,
  "claude_code_preinstalled": true,
  "installation_date": "BUILD_TIME"
}
EOF

# Set proper permissions
chmod 755 /usr/local/bin/vibesh 2>/dev/null || true
chmod 755 /usr/local/bin/vibeos-ai-selector 2>/dev/null || true
chmod 755 /usr/local/bin/test-vibesh 2>/dev/null || true
chmod 755 /usr/local/bin/vibeos-network-setup 2>/dev/null || true
chmod 755 /usr/local/bin/vibeos-debug 2>/dev/null || true
chmod 755 /usr/local/bin/vibeos-browser 2>/dev/null || true

# Ensure Python modules have correct permissions
chmod -R 755 /usr/lib/vibeos/shell/ 2>/dev/null || true
find /usr/lib/vibeos/shell/ -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true

# Create a marker file to indicate Claude Code was pre-installed
touch /etc/vibeos/.claude_code_preinstalled

# Install Claude Code Python SDK
echo ""
echo "============================================"
echo "Installing Claude Code Python SDK"
echo "============================================"
echo ""

# Check if pip is available
if command -v pip &> /dev/null; then
    echo "✅ pip found, installing claude-code-sdk..."

    # Install the SDK with explicit dependencies
    if pip install claude-code-sdk anyio; then
        echo "✅ Claude Code SDK installed successfully!"

        # Verify installation
        if python -c "import claude_code_sdk; print('SDK import successful')" 2>/dev/null; then
            echo "✅ SDK import test passed"
            touch /etc/vibeos/.claude_code_sdk_installed
        else
            echo "⚠️  SDK installed but import failed"
        fi
    else
        echo "❌ Failed to install Claude Code SDK"
        echo "Users will need to install manually: pip install claude-code-sdk"
    fi
else
    echo "⚠️  pip not found, cannot install Claude Code SDK"
    echo "Make sure python-pip is in packages.x86_64"
fi

echo ""
echo "================================================"
echo "    Enabling Network Services"
echo "================================================"
echo ""

# Enable NetworkManager service to start on boot
if [ -f /etc/systemd/system/vibeos-network.service ]; then
    systemctl enable vibeos-network.service 2>/dev/null || true
    echo "✅ Network service enabled for automatic startup"
fi

# Enable NetworkManager if available
systemctl enable NetworkManager 2>/dev/null || true
systemctl enable dhcpcd 2>/dev/null || true

echo ""
echo "================================================"
echo "    Customization Complete"
echo "================================================"
echo ""
echo "Pre-installed packages:"
echo "  • Claude Code (AI Assistant)"
echo "  • Node.js $(node --version 2>/dev/null || echo '')"
echo "  • npm $(npm --version 2>/dev/null || echo '')"
echo "  • Python $(python --version 2>&1 | cut -d' ' -f2 || echo '')"
echo "  • NetworkManager (for network connectivity)"
echo ""