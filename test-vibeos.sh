#!/bin/bash
# VibeOS Testing Script
# Run this after the build completes to test the fixes

echo "================================================"
echo "    VibeOS Boot Test Script"
echo "================================================"
echo ""
echo "This script will:"
echo "1. Build the ISO (if not already built)"
echo "2. Test it in QEMU"
echo ""

# Check if ISO exists
if [ ! -f "output/vibeos-0.1.0-alpha-x86_64.iso" ]; then
    echo "ISO not found. Building first..."
    make build
    if [ $? -ne 0 ]; then
        echo "Build failed. Please check the errors above."
        exit 1
    fi
else
    echo "ISO found at output/vibeos-0.1.0-alpha-x86_64.iso"
fi

echo ""
echo "Starting QEMU test..."
echo "================================"
echo "What to expect:"
echo "1. Arch Linux boot messages (including 'Please configure your system')"
echo "2. Automatic login as root"
echo "3. VibeOS welcome message"
echo "4. vibesh natural language shell should start automatically"
echo ""
echo "Press Ctrl+A then X to exit QEMU"
echo "================================"
echo ""

# Test the ISO
make test