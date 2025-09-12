# VibeOS Build Environment
# Based on Arch Linux with archiso tools for building ISO images

FROM archlinux:latest

# Update system and install build dependencies
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
        archiso \
        base-devel \
        git \
        sudo \
        squashfs-tools \
        libisoburn \
        dosfstools \
        lynx \
        wget \
        vim \
        nano

# Create build user (archiso requires non-root for some operations)
RUN useradd -m -G wheel -s /bin/bash builder && \
    echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Set working directory
WORKDIR /build

# Create output directory for ISO files
RUN mkdir -p /output && \
    chown builder:builder /output

# Switch to builder user
USER builder

# Default command
CMD ["/bin/bash"]