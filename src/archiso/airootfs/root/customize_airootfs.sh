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
echo "NPM version: $(npm --version)"
echo "Node version: $(node --version)"
echo "NPM prefix: $(npm config get prefix)"

# Set npm configuration for chroot environment
export npm_config_prefix=/usr
export npm_config_cache=/tmp/npm-cache
export npm_config_loglevel=verbose

# Create cache directory
mkdir -p /tmp/npm-cache

# Try to install Claude Code with error handling
echo "Installing @anthropic-ai/claude-code..."
if npm install -g @anthropic-ai/claude-code; then
    echo "✅ npm install completed successfully"
else
    echo "❌ npm install failed with exit code $?"
    echo "Attempting alternative installation method..."
    
    # Try with different npm settings
    npm config set registry https://registry.npmjs.org/
    npm config set strict-ssl false
    npm install -g @anthropic-ai/claude-code --verbose || {
        echo "⚠️  Warning: Claude Code installation failed"
        echo "   Users will need to install it manually after boot"
    }
fi

# Verify installation
echo ""
echo "Verifying installation..."
if [ -f /usr/bin/claude-code ]; then
    echo "✅ Claude Code binary found at /usr/bin/claude-code"
    ls -la /usr/bin/claude-code
elif [ -f /usr/local/bin/claude-code ]; then
    echo "✅ Claude Code binary found at /usr/local/bin/claude-code"
    ls -la /usr/local/bin/claude-code
else
    echo "⚠️  Warning: Claude Code binary not found in expected locations"
    echo "Searching for claude-code..."
    find /usr -name "claude-code" 2>/dev/null || echo "Not found in /usr"
fi

# Check if command is available
if command -v claude-code &> /dev/null; then
    echo "✅ Claude Code command is available in PATH"
    echo "   Location: $(which claude-code)"
    echo "   Version: $(claude-code --version 2>/dev/null || echo 'version check failed')"
else
    echo "⚠️  Warning: claude-code command not in PATH"
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

# Ensure Python modules have correct permissions
chmod -R 755 /usr/lib/vibeos/shell/ 2>/dev/null || true
find /usr/lib/vibeos/shell/ -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true

# Create a marker file to indicate Claude Code was pre-installed
touch /etc/vibeos/.claude_code_preinstalled

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
echo ""