#!/bin/bash
# VibeOS ISO Build Script
# Builds the VibeOS ISO using archiso in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "    Building VibeOS ISO"
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
# Copy all Python files including __init__.py and ai_selector
cp -r src/vibeos/shell/*.py src/archiso/airootfs/usr/lib/vibeos/shell/ 2>/dev/null || true
# Ensure __init__.py exists
touch src/archiso/airootfs/usr/lib/vibeos/shell/__init__.py
# Make launcher scripts executable
chmod +x src/archiso/airootfs/usr/local/bin/vibesh 2>/dev/null || true
chmod +x src/archiso/airootfs/usr/local/bin/vibeos-ai-selector 2>/dev/null || true
# Make customize script executable
chmod +x src/archiso/airootfs/root/customize_airootfs.sh 2>/dev/null || true

# Run the build in Docker
echo "Starting ISO build in Docker container..."
echo ""

docker run --rm \
    --privileged \
    -v "$(pwd)/src:/build/src:rw" \
    -v "$(pwd)/output:/output:rw" \
    vibeos-builder:latest \
    bash -c "
        set -e
        echo 'Copying archiso profile...'
        sudo cp -r /build/src/archiso /tmp/vibeos-profile
        
        echo 'Building ISO with archiso...'
        cd /tmp/vibeos-profile
        
        # Standard mkarchiso build - let it handle everything
        sudo mkarchiso -v -w work -o /output .
        
        # Fix permissions on output
        sudo chown -R \$(id -u):\$(id -g) /output
        
        echo ''
        echo 'Build complete!'
    "

# Check if ISO was created
if ls output/*.iso 1> /dev/null 2>&1; then
    ISO_FILE=$(ls -t output/*.iso | head -1)
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    echo ""
    echo "================================================"
    echo -e "${GREEN}✓ Build Successful!${NC}"
    echo "================================================"
    echo ""
    echo "ISO created: $ISO_FILE"
    echo "Size: $ISO_SIZE"
    echo ""
    echo "VibeOS Features:"
    echo "  • Claude Code AI assistant (pre-installed)"
    echo "  • Natural language shell (vibesh)"
    echo "  • AI assistant selector on TTY1"
    echo "  • Debug bash shells on TTY2-TTY6 (Ctrl+Alt+F2-F6)"
    echo "  • Commands like 'create new python project'"
    echo ""
    echo "To test the ISO, run: make test"
else
    echo ""
    echo -e "${RED}✗ Build Failed${NC}"
    echo "No ISO file was created. Check the output above for errors."
    exit 1
fi