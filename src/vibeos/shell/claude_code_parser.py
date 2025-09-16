#!/usr/bin/env python3
"""
Claude Code Integration for VibeOS Shell
Uses Claude Code (with user's subscription) to interpret natural language commands
"""

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List


class ClaudeCodeParser:
    """Parse natural language using Claude Code instead of regex patterns"""

    def __init__(self):
        self.config = self._load_config()
        self.debug_mode = self._is_debug_enabled()

        if self.debug_mode:
            print("[DEBUG] Initializing Claude Code Parser...")
            print(f"[DEBUG] Config loaded: {self.config.get('debug', {})}")

        self.claude_available = self._check_claude_code()
        self.context_file = Path("/tmp/.vibeos_claude_context.json")
        self.conversation_history = []
        self.cache = {} if self.config.get('claude_code', {}).get('cache_commands', True) else None

        if self.debug_mode:
            print(f"[DEBUG] Claude Code available: {self.claude_available}")
            print(f"[DEBUG] Cache enabled: {self.cache is not None}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_path = Path("/etc/vibeos/claude_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        return {
            'debug': {'enabled': True},
            'claude_code': {
                'enabled': True,
                'fallback_to_regex': True,
                'command_timeout': 10
            }
        }

    def _is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled"""
        # Check environment variable first (overrides config)
        env_debug = os.environ.get('VIBEOS_DEBUG', '').lower()
        if env_debug in ['false', '0', 'no', 'off']:
            return False
        if env_debug in ['true', '1', 'yes', 'on']:
            return True

        # Fall back to config file
        return self.config.get('debug', {}).get('enabled', True)

    def _check_claude_code(self) -> bool:
        """Check if Claude Code is installed and accessible"""
        if self.debug_mode:
            print("\n[DEBUG] === Claude Code Detection ===")

        # Method 1: Check if wrapper exists
        wrapper_path = Path("/usr/bin/claude-code")
        if self.debug_mode:
            print(f"[DEBUG] Checking for wrapper at {wrapper_path}...")
            print(f"[DEBUG]   Exists: {wrapper_path.exists()}")
            if wrapper_path.exists():
                print(f"[DEBUG]   Is file: {wrapper_path.is_file()}")
                print(f"[DEBUG]   Is executable: {os.access(str(wrapper_path), os.X_OK)}")

        if wrapper_path.exists():
            if self.debug_mode:
                print("[DEBUG] ✓ Found /usr/bin/claude-code wrapper")
            return True

        # Method 2: Check if Node module exists
        module_path = Path("/usr/lib/node_modules/@anthropic-ai/claude-code")
        if self.debug_mode:
            print(f"[DEBUG] Checking for Node module at {module_path}...")
            print(f"[DEBUG]   Exists: {module_path.exists()}")
            if module_path.exists():
                cli_path = module_path / "cli.js"
                print(f"[DEBUG]   cli.js exists: {cli_path.exists()}")

        if module_path.exists():
            if self.debug_mode:
                print(f"[DEBUG] ✓ Found Claude Code module at {module_path}")
            return True

        # Method 3: Try to run claude-code command
        if self.debug_mode:
            print("[DEBUG] Trying to locate claude-code via 'which' command...")

        try:
            result = subprocess.run(
                ["which", "claude-code"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if self.debug_mode:
                print(f"[DEBUG]   which exit code: {result.returncode}")
                if result.stdout:
                    print(f"[DEBUG]   which output: {result.stdout.strip()}")
                if result.stderr:
                    print(f"[DEBUG]   which stderr: {result.stderr.strip()}")

            if result.returncode == 0:
                if self.debug_mode:
                    print(f"[DEBUG] ✓ claude-code found at {result.stdout.strip()}")
                return True
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Exception running 'which': {e}")

        if self.debug_mode:
            print("[DEBUG] ✗ Claude Code not detected by any method")
            print("[DEBUG] === End Detection ===")
        return False

    def _get_claude_command(self) -> Optional[str]:
        """Get the command to run Claude Code"""
        # Try standard command first
        if subprocess.run(["which", "claude-code"], capture_output=True).returncode == 0:
            return "claude-code"

        # Check known paths
        paths = [
            "/usr/bin/claude-code",
            "/usr/local/bin/claude-code"
        ]
        for path in paths:
            if Path(path).exists() and os.access(path, os.X_OK):
                return path

        # Check for Node.js module
        module_path = "/usr/lib/node_modules/@anthropic-ai/claude-code/cli.js"
        if Path(module_path).exists():
            return f"node {module_path}"

        return None

    def _create_command_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Create a prompt for Claude Code to interpret the command"""
        cwd = context.get('cwd', os.getcwd())

        prompt = f"""You are interpreting natural language commands for VibeOS, a natural language operating system.
The user said: "{user_input}"

Current directory: {cwd}

Your task is to output ONLY the exact shell command(s) that should be executed.
Rules:
1. Output only executable bash commands
2. If multiple commands are needed, separate with && or ;
3. Use absolute paths when possible
4. For ambiguous requests, make reasonable assumptions
5. For project creation, include all necessary setup commands
6. Do not include explanations, only commands

Examples:
User: "create a new python project called myapp"
Output: mkdir myapp && cd myapp && python -m venv venv && echo '#!/usr/bin/env python3\\nprint("Hello from myapp")' > main.py && git init

User: "install pandas"
Output: pip install pandas

User: "show me what's in this folder"
Output: ls -la

Now interpret the user's command and output only the shell command(s):"""

        return prompt

    def parse_with_claude(self, input_text: str, context: Dict[str, Any] = {}) -> Tuple[str, Dict[str, Any]]:
        """
        Use Claude Code to interpret natural language into commands

        Returns:
            Tuple of (intent, parameters)
        """
        if not self.claude_available:
            return 'claude_not_available', {'error': 'Claude Code is not installed or not accessible'}

        # Check cache first
        if self.cache is not None:
            cache_key = f"{input_text.lower().strip()}:{context.get('cwd', '')}"
            if cache_key in self.cache:
                cached_command = self.cache[cache_key]
                return 'execute_command', {
                    'command': cached_command,
                    'original_input': input_text,
                    'from_cache': True
                }

        # Create prompt for Claude
        prompt = self._create_command_prompt(input_text, context)

        try:
            # Create a temporary file with the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                temp_prompt_file = f.name

            # Call Claude Code with the prompt
            # First try the standard command
            claude_cmd = self._get_claude_command()
            if not claude_cmd:
                return 'claude_not_available', {'error': 'Claude Code command not found'}

            # Using echo and pipe to send to Claude Code in non-interactive mode
            result = subprocess.run(
                f"echo '{prompt}' | {claude_cmd} --no-interactive --quiet",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Clean up temp file
            try:
                os.unlink(temp_prompt_file)
            except:
                pass

            if result.returncode == 0 and result.stdout:
                # Extract the command from Claude's response
                command = self._extract_command(result.stdout)
                if command:
                    # Add to conversation history
                    self.conversation_history.append({
                        'input': input_text,
                        'command': command
                    })

                    # Cache the command
                    if self.cache is not None:
                        cache_key = f"{input_text.lower().strip()}:{context.get('cwd', '')}"
                        self.cache[cache_key] = command

                    return 'execute_command', {
                        'command': command,
                        'original_input': input_text
                    }

            # Claude Code couldn't process the command
            return 'claude_error', {
                'error': 'Claude Code could not interpret your command',
                'input': input_text
            }

        except subprocess.TimeoutExpired:
            return 'timeout', {'error': 'Claude Code took too long to respond'}
        except Exception as e:
            return 'error', {'error': str(e)}

    def _extract_command(self, claude_output: str) -> Optional[str]:
        """Extract executable command from Claude's response"""
        lines = claude_output.strip().split('\n')

        # Look for lines that look like commands (not explanations)
        command_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty lines and obvious non-commands
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            # Skip lines that look like explanations
            if any(word in line.lower() for word in ['here', 'this', 'will', 'should', 'would']):
                continue
            # This might be a command
            command_lines.append(line)

        if command_lines:
            # Join multiple commands with &&
            return ' && '.join(command_lines)

        return None

    def _fallback_parse(self, input_text: str) -> Tuple[str, Dict[str, Any]]:
        """No fallback - Claude Code is required"""
        return 'claude_required', {
            'error': 'Claude Code is required to process this command',
            'input': input_text
        }

    def parse(self, input_text: str, context: Dict[str, Any] = {}) -> Tuple[str, Dict[str, Any]]:
        """
        Main parse method that tries Claude Code first, then falls back

        Returns:
            Tuple of (intent, parameters)
        """
        # Claude Code is mandatory - no fallback
        if not self.claude_available:
            return 'claude_not_available', {
                'error': 'Claude Code must be installed and authenticated to use VibeOS',
                'input': input_text
            }

        return self.parse_with_claude(input_text, context)

    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get command suggestions based on partial input and history"""
        suggestions = []
        partial_lower = partial_input.lower()

        # Suggestions based on common patterns
        if partial_lower.startswith('create'):
            suggestions.extend([
                'create a new Python project with tests',
                'create a React app with TypeScript',
                'create a REST API with FastAPI',
                'create a virtual environment'
            ])
        elif partial_lower.startswith('install'):
            suggestions.extend([
                'install the packages I need for data science',
                'install web development tools',
                'install Docker and set it up',
                'install and configure Git'
            ])
        elif partial_lower.startswith('set'):
            suggestions.extend([
                'set up a complete development environment',
                'set up Python for machine learning',
                'set up a database for my project',
                'set up CI/CD pipeline'
            ])
        elif partial_lower.startswith('fix'):
            suggestions.extend([
                'fix the errors in my code',
                'fix Python import issues',
                'fix Git merge conflicts',
                'fix permission problems'
            ])

        # Add suggestions from conversation history
        for item in self.conversation_history[-5:]:
            if partial_lower in item['input'].lower():
                suggestions.append(item['input'])

        return suggestions[:5]

    def clear_context(self):
        """Clear conversation history"""
        self.conversation_history = []
        if self.context_file.exists():
            try:
                self.context_file.unlink()
            except:
                pass