#!/bin/bash
# VibeOS Development Setup Script
# Installs dependencies and prepares the build environment

set -e

echo "================================================"
echo "    VibeOS Development Environment Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Docker
check_docker() {
    echo -n "Checking for Docker... "
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓${NC} Found $(docker --version)"
        return 0
    else
        echo -e "${RED}✗${NC} Not found"
        echo ""
        echo "Docker is required for VibeOS development."
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        return 1
    fi
}

# Check for QEMU
check_qemu() {
    echo -n "Checking for QEMU... "
    if command -v qemu-system-x86_64 &> /dev/null; then
        echo -e "${GREEN}✓${NC} Found $(qemu-system-x86_64 --version | head -n1)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Not found (optional, needed for 'make test')"
        echo "  Install QEMU for VM testing:"
        echo "  - macOS: brew install qemu"
        echo "  - Linux: sudo apt install qemu-system-x86 (or equivalent)"
        echo "  - Windows: Download from https://www.qemu.org/download/"
        return 0  # Don't fail, QEMU is optional
    fi
}

# Build Docker image
build_docker_image() {
    echo ""
    echo "Building VibeOS Docker image..."
    if docker build -t vibeos-builder:latest .; then
        echo -e "${GREEN}✓${NC} Docker image built successfully"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to build Docker image"
        return 1
    fi
}

# Create output directory
create_output_dir() {
    echo -n "Creating output directory... "
    mkdir -p output
    echo -e "${GREEN}✓${NC} Done"
}

# Main setup flow
main() {
    echo "Starting setup..."
    echo ""
    
    # Check dependencies
    check_docker || exit 1
    check_qemu
    
    # Build environment
    build_docker_image || exit 1
    
    # Create directories
    create_output_dir
    
    echo ""
    echo "================================================"
    echo -e "${GREEN}✓ Setup Complete!${NC}"
    echo "================================================"
    echo ""
    echo "You can now use the following commands:"
    echo "  make build  - Build the VibeOS ISO"
    echo "  make test   - Test in QEMU (if installed)"
    echo "  make shell  - Open build environment shell"
    echo ""
    echo "To get started:"
    echo "  1. Run 'make build' to create your first ISO"
    echo "  2. Run 'make test' to boot it in a VM"
    echo ""
}

# Run main function
main