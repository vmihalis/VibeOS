#!/usr/bin/env python3
"""
Diagnostic script to test vibesh module loading
Run this to verify all modules can be imported correctly
"""

import sys
import os

print("VibeOS Module Diagnostic Test")
print("=" * 50)

# Test 1: Check Python version
print(f"Python version: {sys.version}")
print()

# Test 2: Check module paths
print("Module search paths:")
for path in sys.path:
    print(f"  - {path}")
print()

# Test 3: Check if vibeos modules exist
vibeos_path = "/usr/lib/vibeos"
if os.path.exists(vibeos_path):
    print(f"✓ VibeOS path exists: {vibeos_path}")
    shell_path = os.path.join(vibeos_path, "shell")
    if os.path.exists(shell_path):
        print(f"✓ Shell path exists: {shell_path}")
        print("  Files found:")
        for file in os.listdir(shell_path):
            print(f"    - {file}")
    else:
        print(f"✗ Shell path missing: {shell_path}")
else:
    print(f"✗ VibeOS path missing: {vibeos_path}")
    # Try local development path
    local_path = "src/vibeos/shell"
    if os.path.exists(local_path):
        print(f"  Using local path: {local_path}")
        sys.path.insert(0, "src/vibeos")
print()

# Test 4: Try importing modules
print("Testing module imports:")

# Add vibeos to path if needed
if vibeos_path not in sys.path and os.path.exists(vibeos_path):
    sys.path.insert(0, vibeos_path)

try:
    # Test individual module imports
    print("  Testing parser.py...")
    from shell.parser import NaturalLanguageParser
    print("  ✓ NaturalLanguageParser imported")
except ImportError as e:
    print(f"  ✗ Failed to import parser: {e}")

try:
    print("  Testing commands.py...")
    from shell.commands import CommandExecutor
    print("  ✓ CommandExecutor imported")
except ImportError as e:
    print(f"  ✗ Failed to import commands: {e}")

try:
    print("  Testing context.py...")
    from shell.context import ContextManager
    print("  ✓ ContextManager imported")
except ImportError as e:
    print(f"  ✗ Failed to import context: {e}")

try:
    print("  Testing vibesh.py...")
    from shell.vibesh import VibeShell
    print("  ✓ VibeShell imported")
except ImportError as e:
    print(f"  ✗ Failed to import vibesh: {e}")

print()
print("=" * 50)
print("Diagnostic test complete!")
print()
print("If all imports show ✓, vibesh should work correctly.")
print("If any show ✗, those modules need to be fixed.")