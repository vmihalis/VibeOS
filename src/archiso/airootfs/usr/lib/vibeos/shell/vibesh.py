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
import logging
import shlex
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Ensure the module path is set correctly
if '/usr/lib/vibeos' not in sys.path:
    sys.path.insert(0, '/usr/lib/vibeos')

try:
    # Try SDK parser first (new implementation)
    from .claude_sdk_parser import ClaudeSDKParser as ClaudeParser
    print("[VIBEOS] Using Claude SDK Parser (new)")
except ImportError:
    try:
        # Fall back to old subprocess parser
        from .claude_code_parser import ClaudeCodeParser as ClaudeParser
        print("[VIBEOS] Using legacy subprocess parser")
    except ImportError:
        # Last resort - try absolute imports
        try:
            from claude_sdk_parser import ClaudeSDKParser as ClaudeParser
        except ImportError:
            from claude_code_parser import ClaudeCodeParser as ClaudeParser


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

        # Claude Code is mandatory - but we'll offer to install it
        try:
            self.parser = ClaudeParser()
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Failed to initialize parser: {e}")
            self.parser = None

        if not self.parser or not self.parser.claude_available:
            print("\n" + "="*60)
            print("⚠️  Claude Code is REQUIRED to use VibeOS")
            print("="*60)
            print("\nVibeOS cannot function without Claude Code.")
            print("Claude Code needs to be installed.")
            print("\n" + "="*60)

            # Offer automatic installation
            print("\nWould you like to install Claude Code now?")
            print("This will take a few minutes and requires internet connection.")
            response = input("\nInstall Claude Code? (y/n): ").strip().lower()

            if response == 'y':
                print("\nInstalling Claude Code...")
                result = subprocess.run(['/usr/local/bin/vibeos-install-claude'],
                                      capture_output=False, text=True)
                if result.returncode == 0:
                    print("\n✅ Installation successful! Please restart vibesh.")
                    print("Run: exit")
                    print("Then: vibesh")
                    sys.exit(0)
                else:
                    print("\n❌ Installation failed. Please run manually:")
                    print("  vibeos-install-claude")
            else:
                print("\nYou can install Claude Code manually:")
                print("  1. Run: vibeos-install-claude")
                print("  2. Or: npm install -g @anthropic-ai/claude-code")
                print("  3. Then: claude-code auth")

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

    def _sanitize_user_input(self, user_input: str) -> Optional[str]:
        """Sanitize user input to prevent injection attacks"""
        if not user_input or not isinstance(user_input, str):
            return None

        # Basic sanitization
        sanitized = user_input.strip()

        # Length check (reasonable limit for natural language commands)
        if len(sanitized) > 5000:
            logging.warning("User input too long, truncating")
            sanitized = sanitized[:5000]

        # Remove null bytes and other dangerous characters
        sanitized = sanitized.replace('\x00', '').replace('\r', '')

        # Check for obvious injection attempts
        dangerous_patterns = [
            r';\s*rm\s+-rf',  # Dangerous rm commands
            r';\s*sudo\s+rm',  # Sudo rm commands
            r'>\s*/dev/sd[a-z]',  # Writing to disk devices
            r'\$\(.*\)',  # Command substitution
            r'`.*`',  # Backtick command substitution
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logging.warning(f"Dangerous pattern detected in input: {pattern}")
                return None

        return sanitized if sanitized else None

    def _safe_subprocess_run(self, command: List[str], timeout: int = 30, **kwargs) -> subprocess.CompletedProcess:
        """Safely execute subprocess with timeout and error handling"""
        try:
            # Validate command
            if not command or not all(isinstance(arg, str) for arg in command):
                raise ValueError("Invalid command arguments")

            # Set safe defaults
            safe_kwargs = {
                'timeout': timeout,
                'check': False,
                'capture_output': kwargs.get('capture_output', True),
                'text': kwargs.get('text', True)
            }

            if self.debug_mode:
                logging.debug(f"Executing command: {command}")

            result = subprocess.run(command, **safe_kwargs)

            if self.debug_mode:
                logging.debug(f"Command completed with exit code: {result.returncode}")

            return result

        except subprocess.TimeoutExpired:
            logging.error(f"Command timed out after {timeout} seconds: {command}")
            raise
        except (OSError, subprocess.SubprocessError) as e:
            logging.error(f"Process error executing {command}: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error executing {command}: {e}")
            raise

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

        if self.parser and self.parser.claude_available:
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
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            # Git is not available or not in a git repository - this is normal
            if self.debug_mode:
                logging.debug(f"Git branch detection failed: {e}")
            pass
        
        return f"\n[{cwd}{git_info}]\n→ "
    
    def process_input(self, user_input: str) -> bool:
        """Process user input and execute appropriate commands"""
        # Input validation and sanitization
        sanitized_input = self._sanitize_user_input(user_input)
        if not sanitized_input:
            print("⚠️  Invalid or potentially dangerous input detected. Please try again.")
            return True

        # Handle special commands (case-insensitive)
        lower_input = sanitized_input.lower()

        if lower_input in ['exit', 'quit', 'bye']:
            print("Goodbye! Stay in the flow.")
            return False

        if lower_input in ['help', '?']:
            self.show_help()
            return True

        # Handle AI assistant switching
        if any(phrase in lower_input for phrase in ['claude code', 'ai assistant', 'switch to claude', 'launch claude']):
            self.launch_ai_assistant()
            return True

        # Check if Claude Code is available
        if not self.parser or not self.parser.claude_available:
            # Special command to install Claude Code
            if 'install claude' in user_input.lower():
                print("\nInstalling Claude Code...")
                result = subprocess.run(['/usr/local/bin/vibeos-install-claude'],
                                      capture_output=False, text=True)
                if result.returncode == 0:
                    print("\n✅ Installation successful! Please restart vibesh.")
                    return False
                else:
                    print("\n❌ Installation failed. Check your network connection.")
            else:
                print("⚠️  Claude Code is not installed. Commands cannot be processed.")
                print("Type 'install claude' to install it now.")
            return True

        # Parse natural language input with Claude Code
        context_data = {
            'cwd': os.getcwd()
        }

        # Claude Code processes everything (using sanitized input)
        intent, params = self.parser.parse(sanitized_input, context_data)

        # Handle SDK responses
        if intent == "sdk_response":
            # SDK provided a direct response - this IS the conversation
            response = params.get('response', '')
            if response:
                print(f"\n🤖 Claude: {response}")

                # Check if response cached
                if params.get('from_cache'):
                    print("   (from cache)")
            else:
                print("\n❌ Empty response from Claude")
            return True

        # Handle legacy command execution (for backward compatibility)
        elif intent == "execute_command":
            try:
                command = params.get('command', '')
                if not command:
                    print("⚠️  No command provided")
                    return True

                print(f"💭 Executing: {command}")

                # Execute command with proper safety measures
                # Note: This is still using shell=True for compatibility but with sanitized input
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60 second timeout
                    cwd=os.getcwd()
                )

                if result.stdout:
                    print(result.stdout)
                if result.stderr and result.returncode != 0:
                    print(f"⚠️  {result.stderr}")

                return True

            except subprocess.TimeoutExpired:
                print("⚠️  Command timed out after 60 seconds")
                return True
            except (OSError, subprocess.SubprocessError) as e:
                print(f"⚠️  Process error: {e}")
                return True
            except Exception as e:
                print(f"⚠️  Error executing command: {e}")
                return True

        # Handle various error states
        elif intent in ["sdk_not_available", "cli_not_available", "cli_not_found"]:
            print(f"\n❌ {params.get('error', 'Claude Code SDK/CLI is required')}")
            help_text = params.get('help')
            if help_text:
                print(f"\n💡 {help_text}")
            elif not self.parser.claude_available:
                print("\nInstall Claude Code SDK: pip install claude-code-sdk")
                print("Install Claude Code CLI: npm install -g @anthropic-ai/claude-code")
                print("Then authenticate: claude-code auth")
            return True

        elif intent in ["connection_error", "process_error", "json_error", "sdk_error"]:
            print(f"\n❌ Claude Code Error: {params.get('error', 'Unknown error')}")
            if 'exit_code' in params:
                print(f"Exit code: {params['exit_code']}")

            # Provide helpful suggestions based on error type
            if intent == "connection_error":
                print("\n💡 Try: claude-code auth")
            elif intent == "process_error":
                print("\n💡 Check if Claude Code CLI is properly installed")
            return True

        elif intent == "empty_response":
            print(f"\n❌ {params.get('error', 'Claude returned an empty response')}")
            print("💡 Try rephrasing your request or check your internet connection")
            return True

        else:
            # Unexpected response
            print(f"\n❌ Unexpected response type: {intent}")
            if params.get('error'):
                print(f"Error: {params['error']}")
            if self.debug_mode:
                print(f"[DEBUG] Full params: {params}")

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