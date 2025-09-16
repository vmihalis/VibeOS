#!/usr/bin/env python3
"""
VibeOS Natural Language Shell (vibesh)
A shell that understands natural language and maintains developer flow state
"""

import os
import sys
import subprocess
import readline
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Ensure the module path is set correctly
if '/usr/lib/vibeos' not in sys.path:
    sys.path.insert(0, '/usr/lib/vibeos')

try:
    # Try relative imports first (when run as a module)
    from .claude_code_parser import ClaudeCodeParser
except ImportError:
    # Fall back to absolute imports (when run directly)
    from claude_code_parser import ClaudeCodeParser


class VibeShell:
    """Main shell class for VibeOS natural language interface"""
    
    def __init__(self):
        # Check debug mode
        self.debug_mode = os.environ.get('VIBEOS_DEBUG', 'true').lower() in ['true', '1', 'yes', 'on']

        if self.debug_mode:
            print("\n[DEBUG] Initializing VibeOS Shell...")
            print(f"[DEBUG] Python version: {sys.version}")
            print(f"[DEBUG] Working directory: {os.getcwd()}")
            print(f"[DEBUG] PATH: {os.environ.get('PATH', 'not set')}")

        # Claude Code is mandatory - no fallback
        self.parser = ClaudeCodeParser()

        if not self.parser.claude_available:
            print("\n" + "="*60)
            print("⚠️  Claude Code is REQUIRED to use VibeOS")
            print("="*60)
            print("\nVibeOS cannot function without Claude Code.")
            print("Please install and authenticate Claude Code:")
            print("\n  1. Install: npm install -g @anthropic-ai/claude-code")
            print("  2. Authenticate: claude-code auth")
            print("\n" + "="*60)

            if self.debug_mode:
                print("\n[DEBUG] Troubleshooting:")
                print("[DEBUG] Run 'vibeos-debug status' for detailed diagnostics")
                print("[DEBUG] Run 'vibeos-debug fix' to attempt auto-fix")

            print("\nSystem will continue but commands won't work until Claude Code is available.\n")
        else:
            print("🤖 Claude Code active - VibeOS ready for natural language!")
            if self.debug_mode:
                print("[DEBUG] Claude Code detection successful")

        # No executor or context needed - Claude Code handles everything
        self.running = True
        self.history_file = Path.home() / '.vibesh_history'

        # Initialize readline for better input handling
        self._setup_readline()
        
    def _setup_readline(self):
        """Configure readline for command history and tab completion"""
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        
        # Load history if it exists
        if self.history_file.exists():
            readline.read_history_file(str(self.history_file))
        
    def _completer(self, text: str, state: int) -> Optional[str]:
        """Tab completion for common phrases"""
        suggestions = [
            "create new",
            "install",
            "show",
            "run",
            "build",
            "test",
            "git",
            "help",
            "switch to claude code",
            "launch ai assistant",
            "exit"
        ]
        
        options = [s for s in suggestions if s.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    
    def print_banner(self):
        """Display welcome banner"""
        print("\n" + "="*60)
        print("    VibeOS Natural Language Shell v0.2.0")
        print("="*60)

        if self.parser.claude_available:
            print("\n🤖 Claude Code Active - Speak naturally, I understand everything!")
            print("\nExamples of what you can say:")
            print("  • 'set up a complete React project with authentication'")
            print("  • 'install everything I need for machine learning'")
            print("  • 'create a REST API with user management'")
            print("  • 'fix the Python errors in my project'")
            print("  • 'optimize this code for better performance'")
        else:
            print("\n⚠️  Claude Code is not available - VibeOS requires Claude Code to function")
            print("\nTo use VibeOS, you must:")
            print("  1. Install Claude Code: npm install -g @anthropic-ai/claude-code")
            print("  2. Authenticate: claude-code auth")
            print("  3. Restart vibesh")

        print("\nType 'help' for more examples or 'exit' to quit.\n")
    
    def get_prompt(self) -> str:
        """Generate context-aware prompt"""
        cwd = os.getcwd()
        home = str(Path.home())
        
        # Simplify home directory display
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        
        # Check for git repository
        git_info = ""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                git_info = f" ({branch})"
        except:
            pass
        
        return f"\n[{cwd}{git_info}]\n→ "
    
    def process_input(self, user_input: str) -> bool:
        """Process user input and execute appropriate commands"""

        # Handle special commands
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye! Stay in the flow.")
            return False

        if user_input.lower() in ['help', '?']:
            self.show_help()
            return True

        # Handle AI assistant switching
        if any(phrase in user_input.lower() for phrase in ['claude code', 'ai assistant', 'switch to claude', 'launch claude']):
            self.launch_ai_assistant()
            return True

        # Parse natural language input with Claude Code
        context_data = {
            'cwd': os.getcwd()
        }

        # Claude Code processes everything
        intent, params = self.parser.parse(user_input, context_data)

        # Handle Claude Code specific intents
        if intent == "execute_command":
            # Claude Code generated a direct command to execute
            try:
                print(f"💭 Executing: {params['command']}")
                result = subprocess.run(
                    params['command'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                if result.stdout:
                    print(result.stdout)
                if result.stderr and result.returncode != 0:
                    print(f"⚠️  {result.stderr}")
                return True
            except Exception as e:
                print(f"Error executing command: {e}")
                return True

        elif intent in ["claude_not_available", "claude_required", "claude_error"]:
            print(f"\n❌ {params.get('error', 'Claude Code is required')}")
            if not self.parser.claude_available:
                print("\nInstall Claude Code: npm install -g @anthropic-ai/claude-code")
                print("Then authenticate: claude-code auth")
            return True

        else:
            # Any other response from Claude Code parser
            print(f"\n❌ Unexpected response: {intent}")
            if params.get('error'):
                print(f"Error: {params['error']}")

        return True
    
    def show_help(self):
        """Display help information"""
        print("\n" + "="*60)
        print("VibeOS Natural Language Commands")
        print("="*60)
        print("\nAI Assistants:")
        print("  • switch to claude code")
        print("  • launch ai assistant")
        print("  • install claude code")
        print("\nProject Management:")
        print("  • create a new [python/node/react/rust] project called [name]")
        print("  • initialize git repository")
        print("  • create virtual environment")
        print("\nPackage Management:")
        print("  • install [package name]")
        print("  • update system packages")
        print("  • search for [package]")
        print("\nDevelopment:")
        print("  • run tests")
        print("  • build the project")
        print("  • start development server")
        print("  • format code")
        print("\nSystem:")
        print("  • show system information")
        print("  • check disk usage")
        print("  • list running processes")
        print("  • show network status")
        print("\nGit:")
        print("  • git status")
        print("  • commit changes with message [message]")
        print("  • push to remote")
        print("  • show git log")
        print("\nNavigation:")
        print("  • go to [directory]")
        print("  • show current directory")
        print("  • list files")
        print("\n" + "="*60)
    
    def launch_ai_assistant(self):
        """Launch AI assistant selector"""
        print("\n🤖 Launching AI Assistant Selector...")
        try:
            # Try to launch the AI selector
            result = subprocess.run(
                ["/usr/local/bin/vibeos-ai-selector"],
                check=False
            )
            if result.returncode != 0:
                print("Failed to launch AI assistant selector.")
        except FileNotFoundError:
            print("AI assistant selector not found. Claude Code may not be installed yet.")
            print("You can install it manually with: npm install -g @anthropic-ai/claude-code")
        except Exception as e:
            print(f"Error launching AI assistant: {e}")
    
    def run(self):
        """Main shell loop"""
        self.print_banner()
        
        while self.running:
            try:
                # Get user input with custom prompt
                user_input = input(self.get_prompt()).strip()
                
                if not user_input:
                    continue
                
                # Save to history
                readline.write_history_file(str(self.history_file))
                
                # Process the input
                self.running = self.process_input(user_input)
                
            except KeyboardInterrupt:
                print("\n\nUse 'exit' to quit or Ctrl+C again to force quit.")
                try:
                    continue
                except KeyboardInterrupt:
                    print("\nForce quitting...")
                    break
            except EOFError:
                print("\nGoodbye!")
                break


def main():
    """Entry point for vibesh"""
    shell = VibeShell()
    shell.run()


if __name__ == "__main__":
    main()