#!/bin/bash
# VibeOS VM Testing Script
# Launches QEMU to test the built ISO

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "    Testing VibeOS in QEMU"
echo "================================================"
echo ""

# Check for QEMU
if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo -e "${RED}✗${NC} QEMU not found!"
    echo ""
    echo "Please install QEMU:"
    echo "  - macOS: brew install qemu"
    echo "  - Linux: sudo apt install qemu-system-x86"
    echo "  - Windows: Download from https://www.qemu.org/download/"
    exit 1
fi

# Find the latest ISO
if ls output/*.iso 1> /dev/null 2>&1; then
    ISO_FILE=$(ls -t output/*.iso | head -1)
    echo "Found ISO: $ISO_FILE"
else
    echo -e "${RED}✗${NC} No ISO found in output/ directory!"
    echo ""
    echo "Please run 'make build' first to create an ISO."
    exit 1
fi

# VM Configuration
RAM="2G"
CPUS="2"

echo ""
echo "Starting VM with:"
echo "  - RAM: $RAM"
echo "  - CPUs: $CPUS"
echo "  - ISO: $ISO_FILE"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the VM${NC}"
echo ""

# Launch QEMU
# Using both BIOS and UEFI options for better compatibility
qemu-system-x86_64 \
    -m $RAM \
    -smp $CPUS \
    -cdrom "$ISO_FILE" \
    -boot d \
    -enable-kvm 2>/dev/null || \
qemu-system-x86_64 \
    -m $RAM \
    -smp $CPUS \
    -cdrom "$ISO_FILE" \
    -boot d \
    -accel hvf 2>/dev/null || \
qemu-system-x86_64 \
    -m $RAM \
    -smp $CPUS \
    -cdrom "$ISO_FILE" \
    -boot d

echo ""
echo "VM stopped."