#!/bin/bash
# Pre-download Claude Code package for offline installation
# This creates a local .tgz file that can be used if network fails during build

set -e

echo "================================================"
echo "    Pre-downloading Claude Code Package"
echo "================================================"
echo ""

# Check if npm is available on host
if ! command -v npm &> /dev/null; then
    echo "⚠️  npm not found on host system"
    echo "Cannot pre-download Claude Code package"
    exit 0
fi

# Get project root directory first (before changing directories)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET_DIR="$PROJECT_ROOT/src/archiso/airootfs/root"

# Create temp directory for download
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "Downloading Claude Code package..."
if npm pack @anthropic-ai/claude-code 2>/dev/null; then
    PACKAGE_FILE=$(ls anthropic-ai-claude-code-*.tgz 2>/dev/null | head -1)

    if [ -f "$PACKAGE_FILE" ]; then
        # Create target directory and copy package
        mkdir -p "$TARGET_DIR"
        cp "$PACKAGE_FILE" "$TARGET_DIR/claude-code-package.tgz"

        echo "✅ Claude Code package saved for offline installation"
        echo "   Location: src/archiso/airootfs/root/claude-code-package.tgz"
        echo "   Size: $(du -h "$PACKAGE_FILE" | cut -f1)"
        echo ""
        echo "This will be used if online installation fails during ISO build"
    else
        echo "⚠️  Package download succeeded but file not found"
    fi
else
    echo "⚠️  Failed to download Claude Code package"
    echo "Build will attempt online installation"
fi

# Cleanup - use absolute path
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "================================================"
echo "    Package Preparation Complete"
echo "================================================"