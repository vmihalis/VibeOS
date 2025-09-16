#!/bin/bash
# Pre-download Claude Code package for offline installation
# This is a fallback in case network isn't available during ISO build

set -e

echo "================================================"
echo "    Preparing Claude Code for VibeOS"
echo "================================================"
echo ""

# Check if npm is available on host
if ! command -v npm &> /dev/null; then
    echo "⚠️  npm not found on host system"
    echo "Cannot pre-download Claude Code package"
    echo "Build will attempt online installation"
    exit 0
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "Downloading Claude Code package..."
# Use npm pack to download the package as a tarball
if npm pack @anthropic-ai/claude-code; then
    PACKAGE_FILE=$(ls anthropic-ai-claude-code-*.tgz 2>/dev/null | head -1)
    if [ -f "$PACKAGE_FILE" ]; then
        echo "✅ Downloaded: $PACKAGE_FILE"

        # Copy to airootfs for build to use
        TARGET_DIR="$(dirname "$0")/../src/archiso/airootfs/root"
        mkdir -p "$TARGET_DIR"
        cp "$PACKAGE_FILE" "$TARGET_DIR/claude-code-package.tgz"
        echo "✅ Package copied to build directory"
        echo ""
        echo "This package will be used as fallback if online install fails"
    else
        echo "⚠️  Could not find downloaded package"
    fi
else
    echo "⚠️  Failed to download Claude Code package"
    echo "Build will attempt online installation"
fi

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "Preparation complete"