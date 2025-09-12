# VibeOS Development Guide

## Architecture Overview

VibeOS is built on Arch Linux and uses archiso for creating bootable ISO images. The build process runs entirely in Docker to ensure consistency across different development environments.

## Build System

### Docker Container
The build environment is an Arch Linux container with:
- `archiso` - Tool for building Arch Linux live ISO images
- `base-devel` - Basic development tools
- Build user with sudo access (required by archiso)

### archiso Profile
Located in `src/archiso/`, the profile defines:
- **profiledef.sh** - ISO metadata and compression settings
- **packages.x86_64** - List of packages to include
- **airootfs/** - Files to overlay on the root filesystem
- **syslinux/** - BIOS boot configuration
- **efiboot/** - UEFI boot configuration

## Customization Guide

### Adding Packages
Edit `src/archiso/packages.x86_64`:
```bash
# Add your package name on a new line
your-package-name
```

### Adding Custom Files
Place files in `src/archiso/airootfs/` following the filesystem hierarchy:
```
src/archiso/airootfs/
├── etc/
│   ├── hostname           # System hostname
│   └── motd              # Message of the day
├── usr/
│   └── local/
│       └── bin/          # Custom scripts
└── root/                 # Root user's home
```

### Modifying Boot Options
Edit `src/archiso/syslinux/syslinux.cfg` for BIOS boot menu.

## Build Process

1. **Docker Build**: Creates container with Arch Linux + archiso
2. **Profile Copy**: Copies archiso profile to container
3. **mkarchiso**: Runs archiso build process:
   - Downloads packages
   - Creates squashfs filesystem
   - Generates ISO with bootloaders
4. **Output**: ISO saved to `output/` directory

## Testing Workflow

### Local VM Testing
```bash
make test  # Launches QEMU with 2GB RAM
```

### Custom QEMU Options
```bash
qemu-system-x86_64 \
    -m 4G \                    # 4GB RAM
    -smp 4 \                   # 4 CPUs
    -enable-kvm \              # Hardware acceleration
    -cdrom output/vibeos-*.iso
```

### Testing on Real Hardware
1. Write ISO to USB drive:
   ```bash
   sudo dd if=output/vibeos-*.iso of=/dev/sdX bs=4M status=progress
   ```
2. Boot from USB

## Debugging

### Build Issues
```bash
# Open shell in build container
make shell

# Manual archiso build
cd /tmp/vibeos-profile
sudo mkarchiso -v -w work -o /output .
```

### Check Build Logs
The `-v` flag in mkarchiso provides verbose output showing:
- Package downloads
- File system creation
- ISO generation steps

### Common Problems

**"No space left on device"**
- Clean Docker images: `docker system prune`
- Increase Docker disk allocation

**"Permission denied"**
- Ensure Docker is running with proper permissions
- On Linux: Add user to docker group

**"Package not found"**
- Check package name in Arch repositories
- Update container: `docker build --no-cache -t vibeos-builder .`

## Advanced Configuration

### Custom Repository
Add to `src/archiso/pacman.conf`:
```ini
[vibeos]
Server = https://your-repo.com/$arch
```

### Boot Parameters
Edit kernel parameters in `syslinux.cfg`:
```
APPEND archisobasedir=%INSTALL_DIR% quiet splash
```

### Compression Options
Modify in `profiledef.sh`:
```bash
# Faster compression (larger ISO)
airootfs_image_tool_options=('-comp' 'lz4')

# Maximum compression (slower build)
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
```

## Development Best Practices

1. **Test Changes Incrementally**: Build and test after each major change
2. **Use Version Control**: Commit working configurations before experiments
3. **Document Custom Packages**: Explain why each package is included
4. **Keep ISO Minimal**: Start small, add features gradually
5. **Test on Multiple Systems**: VM first, then real hardware

## Future Integration Points

### Natural Language Engine
- Will run as systemd service
- Python-based with LLM integration
- Replaces traditional shell prompt

### Voice Interface
- PulseAudio/PipeWire for audio
- Speech recognition service
- Text-to-speech output

### Custom Shell
- Replace bash with VibeOS interpreter
- Natural language command parsing
- Context-aware responses

## Resources

- [archiso Documentation](https://wiki.archlinux.org/title/Archiso)
- [Arch Linux Packages](https://archlinux.org/packages/)
- [systemd Services](https://wiki.archlinux.org/title/Systemd)
- [QEMU Documentation](https://www.qemu.org/documentation/)