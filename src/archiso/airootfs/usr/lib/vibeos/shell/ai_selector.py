#!/usr/bin/env python3
"""
VibeOS AI Assistant Selector
Manages AI assistant selection and installation
"""

import os
import sys
import subprocess
import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any


class AIAssistantSelector:
    """Manages AI assistant selection and configuration"""
    
    def __init__(self):
        self.config_dir = Path("/etc/vibeos")
        self.config_file = self.config_dir / "ai_config.json"
        self.assistants = {
            "1": {
                "name": "Claude Code",
                "package": "@anthropic-ai/claude-code",
                "command": "claude-code",
                "status": "available",
                "description": "Anthropic's official CLI for Claude - Advanced coding assistant"
            },
            "2": {
                "name": "Gemini CLI",
                "package": None,
                "command": None,
                "status": "coming_soon",
                "description": "Google's Gemini AI assistant - Coming Soon"
            },
            "3": {
                "name": "Codex",
                "package": None,
                "command": None,
                "status": "coming_soon",
                "description": "OpenAI Codex powered assistant - Coming Soon"
            }
        }

    def _validate_config_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data structure"""
        if not isinstance(config, dict):
            return {}

        validated = {}

        # Validate string values
        for key in ['selected_assistant']:
            if key in config and isinstance(config[key], str):
                # Sanitize string values
                sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', config[key])
                if sanitized:
                    validated[key] = sanitized

        # Validate boolean values
        for key in ['auto_launch', 'use_claude_parser']:
            if key in config and isinstance(config[key], bool):
                validated[key] = config[key]

        return validated

    def _validate_user_input(self, user_input: str) -> Optional[str]:
        """Validate and sanitize user input"""
        if not user_input or not isinstance(user_input, str):
            return None

        # Basic sanitization
        sanitized = user_input.strip()

        # Length check
        if len(sanitized) > 100:
            return None

        # Allow only alphanumeric, spaces, and basic punctuation
        if re.match(r'^[a-zA-Z0-9\s\.,\-_]+$', sanitized):
            return sanitized

        return None

    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Try with sudo if needed
            subprocess.run(["sudo", "mkdir", "-p", str(self.config_dir)], check=False)
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError, PermissionError) as e:
                # Config file is corrupted or inaccessible - log warning and use defaults
                logging.warning(f"Failed to load configuration from {self.config_file}: {e}")
                pass
        return {}
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration with validation"""
        # Validate configuration data
        validated_config = self._validate_config_data(config)
        if not validated_config:
            logging.warning("Invalid configuration data, not saving")
            return

        self.ensure_config_dir()
        try:
            with open(self.config_file, 'w') as f:
                json.dump(validated_config, f, indent=2)
        except PermissionError:
            # Try with sudo
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                json.dump(config, tmp, indent=2)
                tmp_path = tmp.name
            subprocess.run(["sudo", "mv", tmp_path, str(self.config_file)], check=False)
    
    def is_claude_code_installed(self) -> bool:
        """Check if Claude Code is installed"""
        # First try direct binary check (more reliable)
        possible_paths = [
            "/usr/bin/claude-code",
            "/usr/local/bin/claude-code",
            "/opt/claude-code/bin/claude-code"
        ]
        
        for path in possible_paths:
            if Path(path).exists() and Path(path).is_file():
                return True
        
        # Fallback to which command if available
        try:
            result = subprocess.run(
                ["which", "claude-code"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # which command not available or timed out
            pass
        
        # Last resort: try to run claude-code directly
        try:
            result = subprocess.run(
                ["claude-code", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_claude_code_preinstalled(self) -> bool:
        """Check if Claude Code was pre-installed during ISO build"""
        marker_file = Path("/etc/vibeos/.claude_code_preinstalled")
        return marker_file.exists()

    def is_claude_code_sdk_installed(self) -> bool:
        """Check if Claude Code SDK was pre-installed during ISO build"""
        marker_file = Path("/etc/vibeos/.claude_code_sdk_installed")
        return marker_file.exists()
    
    def install_claude_code(self) -> bool:
        """Install Claude Code using npm"""
        print("\n📦 Installing Claude Code...")
        print("This may take a moment...\n")
        
        try:
            # Install globally with npm
            result = subprocess.run(
                ["npm", "install", "-g", "@anthropic-ai/claude-code"],
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print("\n✅ Claude Code installed successfully!")
                return True
            else:
                print("\n❌ Failed to install Claude Code")
                print("You can try installing manually later with:")
                print("  npm install -g @anthropic-ai/claude-code")
                return False
        except Exception as e:
            print(f"\n❌ Error installing Claude Code: {e}")
            return False
    
    def display_menu(self):
        """Display AI assistant selection menu"""
        print("\n" + "="*60)
        print("    🤖 VibeOS AI Assistant Selection")
        print("="*60)
        print("\nChoose your AI assistant mode:")
        print("")

        for key, assistant in self.assistants.items():
            status_icon = "✅" if assistant["status"] == "available" else "🔜"
            if assistant["status"] == "available" and assistant["command"]:
                if self.is_claude_code_preinstalled() and self.is_claude_code_sdk_installed():
                    installed = " [Pre-installed & SDK Integrated]"
                elif self.is_claude_code_preinstalled():
                    installed = " [Pre-installed & Integrated]"
                elif self.is_claude_code_installed():
                    installed = " [Installed & Integrated]"
                else:
                    installed = ""
            else:
                installed = ""
            print(f"  {key}. {assistant['name']} {status_icon}{installed}")
            print(f"     {assistant['description']}")
            if key == "1" and self.is_claude_code_installed():
                if self.is_claude_code_sdk_installed():
                    print("     💡 Enhanced with Claude Code SDK for deeper integration")
                else:
                    print("     💡 Powers natural language understanding in vibesh shell")
            print("")

        print("  4. Continue with vibesh (pattern matching mode)")
        print("")
        print("  0. Exit")
        print("\n" + "="*60)
    
    def launch_claude_code(self) -> bool:
        """Launch Claude Code"""
        if not self.is_claude_code_installed():
            if self.is_claude_code_preinstalled():
                print("\n⚠️  Claude Code was pre-installed but may have an issue.")
                print("Please check your system configuration.")
                return False
            else:
                print("\n⚠️  Claude Code is not installed.")
                response = input("Would you like to install it now? (y/n): ").lower()
                if response == 'y':
                    if self.install_claude_code():
                        # Save the choice
                        config = self.load_config()
                        config["selected_assistant"] = "claude-code"
                        config["auto_launch"] = True
                        self.save_config(config)
                    else:
                        return False
                else:
                    return False
        
        print("\n🚀 Launching Claude Code...")
        print("Type 'exit' to return to VibeOS shell\n")
        
        try:
            # Launch Claude Code
            subprocess.run(["claude-code"], check=False)
            return True
        except Exception as e:
            print(f"Error launching Claude Code: {e}")
            return False
    
    def run_selection(self) -> str:
        """Run the selection process and return the chosen assistant"""
        config = self.load_config()
        
        # Check if we have a saved preference and should auto-launch
        if config.get("auto_launch") and config.get("selected_assistant"):
            selected = config["selected_assistant"]
            if selected == "claude-code" and self.is_claude_code_installed():
                print(f"\n🔄 Auto-launching {selected}...")
                print("(Press Ctrl+C within 3 seconds to show menu instead)")
                
                import time
                try:
                    time.sleep(3)
                    return selected
                except KeyboardInterrupt:
                    print("\n\nShowing selection menu...")
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nSelect an option (1-4, 0 to exit): ").strip()
                
                if choice == "0":
                    print("\nExiting...")
                    sys.exit(0)
                
                elif choice == "1":
                    # Claude Code
                    config = self.load_config()
                    config["selected_assistant"] = "claude-code"
                    config["use_claude_parser"] = True
                    config["auto_launch"] = True
                    self.save_config(config)

                    print("\n✅ Claude Code selected!")
                    if self.is_claude_code_sdk_installed():
                        print("🤖 Advanced Claude Code SDK integration enabled in vibesh.")
                        print("\nYou can now:")
                        print("  • Use vibesh with deep Claude Code SDK integration")
                        print("  • Experience enhanced natural language understanding")
                        print("  • Benefit from conversation context and streaming responses")
                        print("  • Launch Claude Code directly by typing 'claude-code'")
                    else:
                        print("🤖 Natural language understanding is now enabled in vibesh.")
                        print("\nYou can now:")
                        print("  • Use vibesh with full natural language understanding")
                        print("  • Launch Claude Code directly by typing 'claude-code'")
                    print("\nStarting vibesh with Claude Code integration...")
                    return "claude-code-integrated"
                
                elif choice in ["2", "3"]:
                    # Coming soon options
                    assistant = self.assistants[choice]
                    print(f"\n🔜 {assistant['name']} is coming soon!")
                    print("Please select another option for now.")
                    input("\nPress Enter to continue...")
                    continue
                
                elif choice == "4":
                    # Continue without AI assistant
                    if self.is_claude_code_installed():
                        print("\n✅ Continuing with VibeOS shell in pattern matching mode...")
                        print("ℹ️  Note: Claude Code is installed but won't be used for natural language.")
                    else:
                        print("\n✅ Continuing with VibeOS natural language shell...")
                    config = self.load_config()
                    config["selected_assistant"] = "vibesh"
                    config["auto_launch"] = False
                    config["use_claude_parser"] = False
                    self.save_config(config)
                    return "vibesh"
                
                else:
                    print("\n❌ Invalid option. Please try again.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\nUse '0' to exit or '4' to continue without AI assistant")
                continue
            except EOFError:
                print("\nExiting...")
                sys.exit(0)


def main():
    """Main entry point for AI assistant selector"""
    selector = AIAssistantSelector()
    selected = selector.run_selection()
    
    if selected == "vibesh":
        # Continue to normal vibesh
        print("\nStarting VibeOS Natural Language Shell...\n")
        # The service will handle launching vibesh after this exits
    elif selected == "claude-code":
        # Claude Code was already launched and exited
        print("\nReturning to VibeOS...")
        # Optionally relaunch vibesh
        response = input("Would you like to start vibesh? (y/n): ").lower()
        if response == 'y':
            import subprocess
            subprocess.run(["/usr/local/bin/vibesh"], check=False)


if __name__ == "__main__":
    main()