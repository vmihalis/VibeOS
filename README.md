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
   git clone https://github.com/vmihalis/VibeOS.git
   cd VibeOS
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

**Note for Apple Silicon (M1/M2) Macs**: The build uses x86_64 emulation via Docker's `--platform` flag. Builds will be slower but fully functional.

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
- ✅ Bootable Arch Linux base system (fixed in latest commit)
- ✅ Consistent build environment using Docker (x86_64 emulation on ARM Macs)
- ✅ Simple command-line interface for building
- ✅ QEMU testing support
- ✅ Natural language shell (vibesh) - understands commands like "create new python project"
- ✅ UEFI and BIOS boot support
- ✅ Proper archiso configuration with mkinitcpio hooks
- ✅ Auto-launch AI assistant selector on boot
- ✅ Claude Code pre-installed - Anthropic's official CLI assistant ready to use
- 🚧 Additional AI assistants (Gemini CLI, Codex - coming soon)

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
2. Ensure enough disk space: `df -h` (need ~10GB free)
3. Clean and retry: `make clean && make build`
4. For debugging: `bash scripts/build-iso-debug.sh`
5. Check if packages installed: Look for "Python installed: 1" in debug output

**Common Issues:**
- **"Failed to mount on real root"**: Missing archiso hooks - rebuild with latest code
- **"No space left"**: Clean Docker: `docker system prune`
- **Slow on M1/M2 Mac**: Normal due to x86 emulation, build takes 5-10 minutes

## VibeOS AI Assistant & Natural Language Interface

### AI Assistant Selection
When you boot VibeOS, you'll be presented with AI assistant options on TTY1:

- **Claude Code** - Anthropic's official CLI for Claude (pre-installed and ready to use)
- **Gemini CLI** - Google's AI assistant (coming soon)
- **Codex** - OpenAI powered assistant (coming soon)

Claude Code comes pre-installed in VibeOS, so you can start using it immediately without any installation or network connection. The system remembers your preference for future boots.

### Natural Language Shell (vibesh)
VibeOS includes a natural language shell that understands commands like:

- **"create a new python project called myapp"** - Sets up a complete Python project structure
- **"install nodejs and npm"** - Automatically detects and uses the right package manager
- **"show system information"** - Displays system status in a friendly format
- **"git status"** - Shows repository status
- **"commit changes with message 'initial commit'"** - Stages and commits
- **"go to Documents folder"** - Natural navigation
- **"create virtual environment"** - Python venv setup
- **"switch to claude code"** - Launch Claude Code AI assistant

### Quick Commands
- Type `ai` in any shell to launch the AI assistant selector
- Type `claude` to directly launch Claude Code (if installed)
- Type `vibeos` to launch the natural language shell

Press `Ctrl+Alt+F2` through `F6` to access debug bash shells if needed.

## Roadmap

- [x] Basic build system
- [x] Docker-based development environment
- [x] Bootable Arch Linux ISO
- [x] Natural language processing engine (basic)
- [x] Custom VibeOS shell (vibesh)
- [x] Claude Code pre-installed (Anthropic's CLI)
- [ ] Additional LLM integrations (Gemini, Codex)
- [ ] Voice input/output support
- [ ] Advanced context awareness
- [ ] Application ecosystem

## License

This project is open source and available under the [MIT License](LICENSE).

## Known Issues

- **Boot failures on first build**: Run `make clean && make build` to ensure proper archiso hooks
- **Slow builds on Apple Silicon**: Due to x86_64 emulation in Docker
- **Natural language shell**: Currently basic regex parsing, LLM integration coming soon

## Support

- **Issues**: [GitHub Issues](https://github.com/vmihalis/VibeOS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vmihalis/VibeOS/discussions)
- **Repository**: [github.com/vmihalis/VibeOS](https://github.com/vmihalis/VibeOS)
- **Documentation**: See the `docs/` directory

---

**Note**: This is an early alpha version focused on establishing the build infrastructure. The natural language interface and core VibeOS features are under active development.