# VibeOS Makefile
# Simple commands for building and testing the OS

.PHONY: help dev-setup build test clean shell

# Default target - show help
help:
	@echo "VibeOS Development Commands:"
	@echo "  make dev-setup  - First time setup (install dependencies)"
	@echo "  make build      - Build the OS ISO"
	@echo "  make test       - Test in QEMU virtual machine"
	@echo "  make shell      - Open build environment shell"
	@echo "  make clean      - Clean build artifacts"

# First time setup - install dependencies and build Docker image
dev-setup:
	@echo "Setting up VibeOS development environment..."
	@bash scripts/setup.sh

# Build the OS ISO
build:
	@echo "Building VibeOS ISO..."
	@bash scripts/build-iso.sh

# Test in virtual machine using QEMU
test:
	@echo "Starting VibeOS in QEMU..."
	@bash scripts/test-vm.sh

# Open interactive shell in build environment
shell:
	@echo "Opening build environment shell..."
	@docker run -it --rm \
		-v $(PWD)/src:/build/src \
		-v $(PWD)/output:/output \
		vibeos-builder:latest \
		/bin/bash

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf output/*
	@rm -rf src/archiso/work
	@echo "Clean complete."