# VibeOS

An open source operating system that replaces traditional UI with natural language interaction.

## Quick Start

### Prerequisites

- **Docker** - Required for consistent build environment
- **QEMU** (optional) - For testing the OS in a virtual machine
- **4GB+ RAM** - For building the ISO
- **10GB+ disk space** - For build artifacts

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vibeos/vibeos.git
   cd vibeos
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```
   This will:
   - Check for required dependencies
   - Build the Docker container with Arch Linux and archiso
   - Create necessary directories

3. **Build the OS:**
   ```bash
   make build
   ```
   This creates a bootable ISO in the `output/` directory.

4. **Test in a VM (requires QEMU):**
   ```bash
   make test
   ```
   This boots the ISO in a QEMU virtual machine.

## Available Commands

| Command | Description |
|---------|-------------|
| `make dev-setup` | First-time setup - installs dependencies and builds Docker image |
| `make build` | Build the VibeOS ISO |
| `make test` | Test the ISO in QEMU virtual machine |
| `make shell` | Open interactive shell in build environment |
| `make clean` | Remove build artifacts |
| `make help` | Show all available commands |

## Project Structure

```
VibeOS/
├── Dockerfile           # Arch Linux build environment
├── Makefile            # Build automation
├── scripts/            # Build and test scripts
│   ├── setup.sh        # Development setup
│   ├── build-iso.sh    # ISO building
│   └── test-vm.sh      # VM testing
├── src/
│   └── archiso/        # Arch ISO configuration
│       ├── airootfs/   # Root filesystem overlay
│       ├── packages.x86_64  # Package list
│       └── profiledef.sh     # ISO profile
├── output/             # Built ISO files (created by build)
└── docs/               # Documentation
```

## System Requirements

### For Building
- Docker installed and running
- 4GB RAM minimum
- 10GB free disk space

### For Testing (Optional)
- QEMU installed (`qemu-system-x86_64`)
- 2GB RAM for VM
- Hardware virtualization support (KVM/HVF) recommended

## Installing Dependencies

### macOS
```bash
brew install --cask docker
brew install qemu  # Optional, for testing
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install docker.io
sudo apt install qemu-system-x86  # Optional, for testing
```

### Linux (Arch)
```bash
sudo pacman -S docker
sudo pacman -S qemu  # Optional, for testing
```

## Current Status

This is a **v0.1.0-alpha** development build that provides:
- ✅ Bootable Arch Linux base system
- ✅ Consistent build environment using Docker
- ✅ Simple command-line interface for building
- ✅ QEMU testing support
- ✅ Natural language shell (vibesh) - understands commands like "create new python project"
- ✅ Auto-launches on boot (TTY1) with regular bash on other TTYs for debugging
- 🚧 LLM integration for advanced AI assistance (coming soon)

## Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run `make dev-setup` to set up your environment
4. Make your changes
5. Test with `make build && make test`
6. Commit your changes
7. Push to your branch
8. Open a Pull Request

## Development Tips

### Opening a Build Shell
To debug or manually run archiso commands:
```bash
make shell
```

### Customizing the ISO
- Edit `src/archiso/packages.x86_64` to add/remove packages
- Modify `src/archiso/profiledef.sh` to change ISO metadata
- Add files to `src/archiso/airootfs/` to include them in the root filesystem

### Build Troubleshooting
If the build fails:
1. Check Docker is running: `docker ps`
2. Ensure enough disk space: `df -h`
3. Clean and retry: `make clean && make build`
4. Check build logs in the Docker output

## VibeOS Natural Language Interface

When you boot VibeOS, you'll see the natural language shell (vibesh) on TTY1. You can speak naturally:

- **"create a new python project called myapp"** - Sets up a complete Python project structure
- **"install nodejs and npm"** - Automatically detects and uses the right package manager
- **"show system information"** - Displays system status in a friendly format
- **"git status"** - Shows repository status
- **"commit changes with message 'initial commit'"** - Stages and commits
- **"go to Documents folder"** - Natural navigation
- **"create virtual environment"** - Python venv setup

Press `Ctrl+Alt+F2` through `F6` to access debug bash shells if needed.

## Roadmap

- [x] Basic build system
- [x] Docker-based development environment
- [x] Bootable Arch Linux ISO
- [x] Natural language processing engine (basic)
- [x] Custom VibeOS shell (vibesh)
- [ ] LLM integration (Claude, GPT, Ollama)
- [ ] Voice input/output support
- [ ] Advanced context awareness
- [ ] Application ecosystem

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

- **Issues**: [GitHub Issues](https://github.com/vibeos/vibeos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vibeos/vibeos/discussions)
- **Documentation**: See the `docs/` directory

---

**Note**: This is an early alpha version focused on establishing the build infrastructure. The natural language interface and core VibeOS features are under active development.