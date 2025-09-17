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
import logging
import shlex
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List


class ClaudeCodeParser:
    """Parse natural language using Claude Code instead of regex patterns"""

    def __init__(self) -> None:
        """Initialize Claude Code Parser with shared utilities."""
        try:
            from .utils import VibeOSConfig, VibeOSDebug, VibeOSContextManager
        except ImportError:
            # Fall back to absolute import for standalone execution
            from utils import VibeOSConfig, VibeOSDebug, VibeOSContextManager
        
        # Load configuration using shared utility
        default_config = {
            'debug': {'enabled': True},
            'claude_code': {
                'enabled': True,
                'fallback_to_regex': True,
                'command_timeout': 10,
                'max_retries': 3,
                'cache_commands': True,
                'cache_ttl': 3600
            }
        }
        self.config = VibeOSConfig.load_config(default_config=default_config)
        
        # Set up debug mode using shared utility
        self.debug_mode = VibeOSDebug.is_debug_enabled(self.config)
        
        # Set up logging
        VibeOSDebug.setup_logging(self.debug_mode)

        if self.debug_mode:
            logging.info("Initializing Claude Code Parser...")
            logging.debug(f"Config loaded: {self.config.get('debug', {})}")

        self.claude_available = self._check_claude_code()
        
        # Use shared context manager
        cache_enabled = self.config.get('claude_code', {}).get('cache_commands', True)
        cache_ttl = self.config.get('claude_code', {}).get('cache_ttl', 3600)
        self.context_manager = VibeOSContextManager(
            cache_enabled=cache_enabled,
            cache_ttl=cache_ttl
        )

        if self.debug_mode:
            logging.debug(f"Claude Code available: {self.claude_available}")
            logging.debug(f"Cache enabled: {cache_enabled}")

    def _validate_config(self, config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration values and apply bounds checking"""
        validated = defaults.copy()

        try:
            # Validate claude_code section
            if 'claude_code' in config:
                claude_config = config['claude_code']
                if isinstance(claude_config, dict):
                    # Validate timeout (1-120 seconds)
                    timeout = claude_config.get('command_timeout', defaults['claude_code']['command_timeout'])
                    if isinstance(timeout, (int, float)) and 1 <= timeout <= 120:
                        validated['claude_code']['command_timeout'] = int(timeout)

                    # Validate max_retries (0-10)
                    retries = claude_config.get('max_retries', defaults['claude_code']['max_retries'])
                    if isinstance(retries, int) and 0 <= retries <= 10:
                        validated['claude_code']['max_retries'] = retries

                    # Validate cache_ttl (60-86400 seconds)
                    cache_ttl = claude_config.get('cache_ttl', defaults['claude_code']['cache_ttl'])
                    if isinstance(cache_ttl, int) and 60 <= cache_ttl <= 86400:
                        validated['claude_code']['cache_ttl'] = cache_ttl

                    # Copy boolean values
                    for key in ['enabled', 'fallback_to_regex', 'cache_commands']:
                        if key in claude_config and isinstance(claude_config[key], bool):
                            validated['claude_code'][key] = claude_config[key]

            # Validate debug section
            if 'debug' in config and isinstance(config['debug'], dict):
                if 'enabled' in config['debug'] and isinstance(config['debug']['enabled'], bool):
                    validated['debug']['enabled'] = config['debug']['enabled']

        except Exception as e:
            logging.warning(f"Configuration validation failed, using defaults: {e}")

        return validated

    def _sanitize_input(self, text: str) -> Optional[str]:
        """Sanitize user input to prevent injection attacks"""
        if not text or not isinstance(text, str):
            return None

        # Remove or escape dangerous characters
        text = text.strip()

        # Basic length check
        if len(text) > 10000:  # Reasonable limit
            logging.warning("Input too long, truncating")
            text = text[:10000]

        # Check for common injection patterns
        dangerous_patterns = [
            r'[;&|`$()]',  # Shell metacharacters
            r'\\x[0-9a-fA-F]{2}',  # Hex escape sequences
            r'\\[0-7]{3}',  # Octal escape sequences
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text):
                # Replace with safe equivalents
                text = re.sub(r'[;&|`$()]', ' ', text)
                text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)
                text = re.sub(r'\\[0-7]{3}', '', text)
                break

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text if text else None

    def _get_validated_timeout(self) -> int:
        """Get timeout value with bounds checking"""
        timeout = self.config.get('claude_code', {}).get('command_timeout', 10)
        return max(1, min(120, int(timeout)))

    def _build_claude_command(self, claude_cmd: str, prompt_file: str) -> List[str]:
        """Build secure command arguments for Claude Code execution"""
        try:
            # Validate file path
            prompt_path = Path(prompt_file)
            if not prompt_path.exists() or not prompt_path.is_file():
                raise ValueError(f"Invalid prompt file: {prompt_file}")

            # Build command safely
            if claude_cmd.startswith('node '):
                # Node.js execution
                node_script = claude_cmd[5:]  # Remove 'node ' prefix
                return ['node', node_script, '--no-interactive', '--quiet', '--file', str(prompt_path)]
            else:
                # Direct claude-code execution
                return [claude_cmd, '--no-interactive', '--quiet', '--file', str(prompt_path)]

        except Exception as e:
            logging.error(f"Failed to build Claude command: {e}")
            raise

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with validation - DEPRECATED: Use shared utilities."""
        # This method is kept for compatibility but redirects to shared utilities
        from .utils import VibeOSConfig
        return VibeOSConfig.load_config()

    def _is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled - DEPRECATED: Use shared utilities."""
        # This method is kept for compatibility but redirects to shared utilities
        from .utils import VibeOSDebug
        return VibeOSDebug.is_debug_enabled(self.config)

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
        """Get the command to run Claude Code using shared utilities."""
        from .utils import VibeOSPathUtils
        return VibeOSPathUtils.resolve_claude_command()

    def _create_command_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Create a prompt for Claude Code to interpret the command"""
        # Validate and sanitize context
        try:
            cwd = context.get('cwd', os.getcwd())
            # Validate the current working directory
            cwd_path = Path(cwd)
            if not cwd_path.exists():
                cwd = os.getcwd()  # Fall back to actual current directory
        except (OSError, PermissionError):
            cwd = "/tmp"  # Safe fallback

        # Escape user input for safe inclusion in prompt
        safe_user_input = user_input.replace('"', '\\"').replace('\n', ' ')

        prompt = f"""You are interpreting natural language commands for VibeOS, a natural language operating system.
The user said: "{safe_user_input}"

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
        Use Claude Code to interpret natural language into commands using shared utilities.

        Args:
            input_text: User's natural language input
            context: Context information including working directory

        Returns:
            Tuple of (intent, parameters) indicating the result
        """
        try:
            from .utils import VibeOSPathUtils, validate_input
        except ImportError:
            from utils import VibeOSPathUtils, validate_input
        
        if not self.claude_available:
            return 'claude_not_available', {'error': 'Claude Code is not installed or not accessible'}

        # Validate and sanitize input using shared utility
        try:
            sanitized_input = validate_input(input_text)
        except ValueError as e:
            return 'input_error', {'error': str(e)}

        # Check cache first using context manager
        cache_key = self.context_manager.create_cache_key(input_text, context)
        cached_response = self.context_manager.get_cached_response(cache_key)
        if cached_response:
            return 'execute_command', {
                'command': cached_response['response'],
                'original_input': input_text,
                'from_cache': True
            }

        # Create prompt for Claude
        prompt = self._create_command_prompt(sanitized_input, context)

        try:
            # Get Claude command first to fail fast
            claude_cmd = VibeOSPathUtils.resolve_claude_command()
            if not claude_cmd:
                return 'claude_not_available', {'error': 'Claude Code command not found'}

            # Get timeout from config with bounds checking
            timeout = self._get_validated_timeout()

            # Execute with retry logic
            max_retries = self.config.get('claude_code', {}).get('max_retries', 3)
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    # Use safer command construction
                    result = subprocess.run(
                        [claude_cmd, '--no-interactive', '--quiet'],
                        input=prompt,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False
                    )

                    # If successful, break out of retry loop
                    if result.returncode == 0:
                        break
                    else:
                        last_error = f"Claude Code returned exit code {result.returncode}: {result.stderr}"
                        if attempt < max_retries:
                            logging.warning(f"Claude Code attempt {attempt + 1} failed, retrying...")
                            continue

                except subprocess.TimeoutExpired as e:
                    last_error = f"Claude Code timed out after {timeout} seconds"
                    if attempt < max_retries:
                        logging.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                        continue
                    else:
                        return 'timeout', {'error': last_error}

                except (OSError, subprocess.SubprocessError) as e:
                    last_error = f"Process error: {str(e)}"
                    if attempt < max_retries:
                        logging.warning(f"Process error on attempt {attempt + 1}, retrying...")
                        continue

            else:
                # All retries exhausted
                return 'process_error', {'error': f"Failed after {max_retries + 1} attempts: {last_error}"}

            if result.returncode == 0 and result.stdout:
                # Extract the command from Claude's response
                command = self._extract_command(result.stdout)
                if command:
                    # Add to conversation history using context manager
                    self.context_manager.add_to_history(input_text, command)

                    # Cache the command using context manager
                    self.context_manager.cache_response(cache_key, command)

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
            logging.error(f"Unexpected error in parse_with_claude: {e}")
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
        # Input validation
        if not input_text or not isinstance(input_text, str):
            return 'input_error', {'error': 'Input must be a non-empty string'}

        # Sanitize input
        sanitized_input = self._sanitize_input(input_text.strip())
        if not sanitized_input:
            return 'input_error', {'error': 'Input contains dangerous or invalid characters'}

        # Validate context
        if not isinstance(context, dict):
            context = {}

        # Claude Code is mandatory - no fallback
        if not self.claude_available:
            return 'claude_not_available', {
                'error': 'Claude Code must be installed and authenticated to use VibeOS',
                'input': sanitized_input
            }

        return self.parse_with_claude(sanitized_input, context)

    def get_suggestions(self, partial_input: str) -> List[str]:
        """
        Get command suggestions based on partial input and history using shared utilities.
        
        Args:
            partial_input: Partial user input text
            
        Returns:
            List of suggested commands (up to 5)
        """
        try:
            from .utils import BaseSuggestionEngine, validate_input
        except ImportError:
            from utils import BaseSuggestionEngine, validate_input
        
        # Input validation using shared utility
        try:
            safe_input = validate_input(partial_input)
        except ValueError:
            return []
        
        # Use shared suggestion engine
        suggestion_engine = BaseSuggestionEngine(self.context_manager)
        return suggestion_engine.get_suggestions(safe_input)

    def clear_context(self) -> None:
        """Clear conversation history using shared context manager."""
        self.context_manager.clear_context()