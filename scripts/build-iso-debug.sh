#!/bin/bash
# VibeOS ISO Build Script with Debugging
# Builds the VibeOS ISO with extensive debugging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "    Building VibeOS ISO (Debug Mode)"
echo "================================================"
echo ""

# Check if Docker image exists
if ! docker images | grep -q "vibeos-builder"; then
    echo -e "${YELLOW}⚠${NC} Docker image not found. Running setup first..."
    bash scripts/setup.sh || exit 1
fi

# Clean previous build artifacts
echo "Cleaning previous build..."
rm -rf src/archiso/work
mkdir -p output

# Ensure shell modules are in place
echo "Copying VibeOS shell modules..."
mkdir -p src/archiso/airootfs/usr/lib/vibeos/shell
cp -r src/vibeos/shell/*.py src/archiso/airootfs/usr/lib/vibeos/shell/ 2>/dev/null || true

# Run the build in Docker with debugging
echo "Starting ISO build in Docker container (debug mode)..."
echo ""

docker run --rm \
    --privileged \
    -v "$(pwd)/src:/build/src:rw" \
    -v "$(pwd)/output:/output:rw" \
    vibeos-builder:latest \
    bash -c "
        set -x  # Enable debug output
        
        echo '=== Copying archiso profile ==='
        sudo cp -r /build/src/archiso /tmp/vibeos-profile
        
        echo '=== Checking pacman configuration ==='
        cat /tmp/vibeos-profile/pacman.conf
        
        echo '=== Package list (first 10 packages) ==='
        head -20 /tmp/vibeos-profile/packages.x86_64
        
        echo '=== Total packages to install ==='
        grep -v '^#' /tmp/vibeos-profile/packages.x86_64 | grep -v '^$' | wc -l
        
        echo '=== Creating work directory ==='
        cd /tmp/vibeos-profile
        mkdir -p work/x86_64/airootfs
        
        echo '=== Installing packages with pacstrap ==='
        # Try to manually install packages first
        sudo pacstrap -c -G -M work/x86_64/airootfs \$(grep -v '^#' packages.x86_64 | grep -v '^$' | tr '\n' ' ')
        
        echo '=== Checking if packages were installed ==='
        ls -la work/x86_64/airootfs/usr/bin/ | head -20
        
        echo '=== Checking for Python ==='
        if [ -f work/x86_64/airootfs/usr/bin/python ]; then
            echo 'Python found!'
        else
            echo 'ERROR: Python NOT found!'
        fi
        
        echo '=== Now building ISO with mkarchiso ==='
        sudo mkarchiso -v -w work -o /output .
        
        # Fix permissions on output
        sudo chown -R \$(id -u):\$(id -g) /output
        
        echo ''
        echo '=== Build complete ==='
    "

# Check if ISO was created
if ls output/*.iso 1> /dev/null 2>&1; then
    ISO_FILE=$(ls -t output/*.iso | head -1)
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    echo ""
    echo "================================================"
    echo -e "${GREEN}✓ ISO Created${NC}"
    echo "================================================"
    echo ""
    echo "ISO file: $ISO_FILE"
    echo "Size: $ISO_SIZE"
    echo ""
    echo "Test with: make test"
else
    echo ""
    echo -e "${RED}✗ Build Failed${NC}"
    echo "No ISO file was created. Check the debug output above."
    exit 1
fi