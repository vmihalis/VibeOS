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
    from .parser import NaturalLanguageParser
    from .commands import CommandExecutor
    from .context import ContextManager
except ImportError:
    # Fall back to absolute imports (when run directly)
    from parser import NaturalLanguageParser
    from commands import CommandExecutor
    from context import ContextManager


class VibeShell:
    """Main shell class for VibeOS natural language interface"""
    
    def __init__(self):
        self.parser = NaturalLanguageParser()
        self.executor = CommandExecutor()
        self.context = ContextManager()
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
            "exit"
        ]
        
        options = [s for s in suggestions if s.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    
    def print_banner(self):
        """Display welcome banner"""
        print("\n" + "="*60)
        print("    VibeOS Natural Language Shell v0.1.0")
        print("="*60)
        print("\nSpeak naturally. I understand commands like:")
        print("  • 'create a new python project called myapp'")
        print("  • 'install nodejs and npm'")
        print("  • 'show system information'")
        print("  • 'git status of current project'")
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
        
        # Parse natural language input
        intent, params = self.parser.parse(user_input)
        
        if intent == "unknown":
            print(f"I'm not sure how to '{user_input}'.")
            print("Try rephrasing or type 'help' for examples.")
            return True
        
        # Execute the command
        try:
            result = self.executor.execute(intent, params, self.context)
            
            if result.get('success'):
                if result.get('output'):
                    print(result['output'])
            else:
                print(f"Error: {result.get('error', 'Command failed')}")
                
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        return True
    
    def show_help(self):
        """Display help information"""
        print("\n" + "="*60)
        print("VibeOS Natural Language Commands")
        print("="*60)
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