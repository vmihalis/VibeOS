#!/usr/bin/env python3
"""
Test script for Claude Code SDK integration in VibeOS
"""

import sys
import os
from pathlib import Path

# Add the vibeos shell path
sys.path.insert(0, 'src/vibeos/shell')

def test_sdk_import():
    """Test if the SDK can be imported"""
    print("Testing Claude Code SDK import...")
    try:
        import anyio
        from claude_code_sdk import query, ClaudeCodeOptions
        print("✅ Claude Code SDK import successful")
        return True
    except ImportError as e:
        print(f"❌ Claude Code SDK import failed: {e}")
        return False

def test_parser_import():
    """Test if our SDK parser can be imported"""
    print("\nTesting Claude SDK Parser import...")
    try:
        from claude_sdk_parser import ClaudeSDKParser
        print("✅ Claude SDK Parser import successful")
        return True
    except ImportError as e:
        print(f"❌ Claude SDK Parser import failed: {e}")
        return False

def test_parser_initialization():
    """Test parser initialization"""
    print("\nTesting Claude SDK Parser initialization...")
    try:
        from claude_sdk_parser import ClaudeSDKParser
        parser = ClaudeSDKParser()
        print(f"✅ Parser initialized successfully")
        print(f"   SDK Available: {parser.sdk_available}")
        print(f"   CLI Available: {parser.claude_available}")
        return parser
    except Exception as e:
        print(f"❌ Parser initialization failed: {e}")
        return None

def test_simple_query(parser):
    """Test a simple query if possible"""
    if not parser or not parser.sdk_available:
        print("\n⚠️  Skipping query test - SDK not available")
        return

    print("\nTesting simple query...")
    try:
        intent, params = parser.parse("hello world", {'cwd': os.getcwd()})
        print(f"✅ Query successful")
        print(f"   Intent: {intent}")
        print(f"   Params keys: {list(params.keys())}")
    except Exception as e:
        print(f"❌ Query failed: {e}")

def test_vibesh_import():
    """Test if vibesh can import the new parser"""
    print("\nTesting VibeShell import with SDK parser...")
    try:
        from vibesh import VibeShell
        shell = VibeShell()
        print(f"✅ VibeShell imported successfully")
        print(f"   Parser type: {type(shell.parser).__name__}")
        print(f"   Claude available: {shell.parser.claude_available}")
        return True
    except Exception as e:
        print(f"❌ VibeShell import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("    VibeOS Claude Code SDK Integration Test")
    print("=" * 60)

    results = []

    # Test 1: SDK import
    results.append(test_sdk_import())

    # Test 2: Parser import
    results.append(test_parser_import())

    # Test 3: Parser initialization
    parser = test_parser_initialization()
    results.append(parser is not None)

    # Test 4: Simple query (only if SDK available)
    test_simple_query(parser)

    # Test 5: VibeShell integration
    results.append(test_vibesh_import())

    # Summary
    print("\n" + "=" * 60)
    print("    Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("🎉 All tests passed! SDK integration is ready.")
    else:
        print("⚠️  Some tests failed. Check the installation.")

    print("\nNext steps:")
    print("1. Build the VibeOS ISO: make build")
    print("2. Test in VM: make test")
    print("3. Try natural language commands in vibesh")

if __name__ == "__main__":
    main()