#!/usr/bin/env python3
"""
Claude Code SDK Integration for VibeOS Shell
Uses the official Claude Code SDK for programmatic access to Claude
"""

import os
import sys
import json
import asyncio
import tempfile
import logging
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, AsyncGenerator
import time

# Try to import the Claude Code SDK
try:
    import anyio
    from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock
    from claude_code_sdk import ClaudeSDKError, CLINotFoundError, CLIConnectionError, ProcessError, CLIJSONDecodeError
    SDK_AVAILABLE = True
except ImportError as e:
    SDK_AVAILABLE = False
    print(f"Warning: Claude Code SDK not available: {e}")


class ClaudeSDKParser:
    """Parse natural language using Claude Code SDK instead of subprocess calls"""

    def __init__(self) -> None:
        """Initialize Claude SDK Parser with shared utilities."""
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
                'fallback_to_regex': False,
                'command_timeout': 30,
                'max_turns': 3,
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
            logging.info("Initializing Claude SDK Parser...")
            logging.debug(f"SDK Available: {SDK_AVAILABLE}")
            logging.debug(f"Config loaded: {self.config.get('debug', {})}")

        # SDK requires both the Python module AND the CLI to be available
        self.sdk_available = SDK_AVAILABLE and self._check_claude_code()
        
        # Use shared context manager
        cache_enabled = self.config.get('claude_code', {}).get('cache_commands', True)
        cache_ttl = self.config.get('claude_code', {}).get('cache_ttl', 3600)
        self.context_manager = VibeOSContextManager(
            cache_enabled=cache_enabled,
            cache_ttl=cache_ttl
        )

        if self.debug_mode:
            logging.debug(f"Claude SDK available: {self.sdk_available}")
            logging.debug(f"Cache enabled: {cache_enabled}")

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
                'fallback_to_regex': False,
                'command_timeout': 30,
                'max_turns': 3
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

    def _validate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize context dictionary"""
        if not isinstance(context, dict):
            return {}

        validated = {}

        # Validate working directory
        cwd = context.get('cwd')
        if cwd and isinstance(cwd, str):
            try:
                cwd_path = Path(cwd)
                if cwd_path.exists() and cwd_path.is_dir():
                    validated['cwd'] = str(cwd_path.absolute())
                else:
                    validated['cwd'] = os.getcwd()
            except (OSError, PermissionError):
                validated['cwd'] = os.getcwd()
        else:
            validated['cwd'] = os.getcwd()

        return validated

    def _check_claude_code(self) -> bool:
        """Check if Claude Code CLI is available for the SDK to use"""
        if not SDK_AVAILABLE:
            return False

        if self.debug_mode:
            print("\n[DEBUG] === Claude Code CLI Detection for SDK ===")

        # The SDK requires the Claude Code CLI to be installed
        try:
            import subprocess
            result = subprocess.run(
                ["which", "claude-code"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if self.debug_mode:
                print(f"[DEBUG] which claude-code exit code: {result.returncode}")
                if result.stdout:
                    print(f"[DEBUG] CLI found at: {result.stdout.strip()}")

            if result.returncode == 0:
                if self.debug_mode:
                    print("[DEBUG] ✓ Claude Code CLI available for SDK")
                return True
            else:
                if self.debug_mode:
                    print("[DEBUG] ✗ Claude Code CLI not found")
                return False

        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Exception checking CLI: {e}")
            return False

    def _create_vibeos_system_prompt(self) -> str:
        """Create a system prompt optimized for VibeOS operations"""
        return """You are the VibeOS natural language shell interpreter. VibeOS is an operating system that replaces traditional GUIs with natural language interaction.

Your role is to:
1. Interpret user commands in natural language
2. Execute appropriate system operations
3. Provide helpful feedback and guidance
4. Maintain awareness of the current working directory and system state

You have access to all system tools including:
- File operations (Read, Write, Edit, Glob, Grep)
- Shell commands (Bash)
- Development tools (package managers, git, build tools)
- System management (processes, services, network)

Guidelines:
- Be concise but helpful
- Execute commands directly when the intent is clear
- Ask for clarification only when truly ambiguous
- Provide context-aware suggestions
- Handle errors gracefully and suggest solutions
- Maintain conversation context for complex multi-step tasks

Current environment: VibeOS Natural Language Shell
Working directory will be provided with each command."""

    async def _query_claude_sdk(self, user_input: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Use Claude Code SDK to process natural language input"""

        if not self.sdk_available:
            return 'sdk_not_available', {'error': 'Claude Code SDK is not installed or configured'}

        try:
            # Prepare options for Claude Code
            options = ClaudeCodeOptions(
                system_prompt=self._create_vibeos_system_prompt(),
                max_turns=self.config.get('claude_code', {}).get('max_turns', 3),
                cwd=context.get('cwd', os.getcwd())
            )

            # Add working directory context to the prompt
            cwd = context.get('cwd', os.getcwd())
            contextual_prompt = f"Current working directory: {cwd}\n\nUser request: {user_input}"

            if self.debug_mode:
                print(f"[DEBUG] Sending to Claude SDK: {contextual_prompt}")
                print(f"[DEBUG] Working directory: {cwd}")

            # Query Claude Code SDK
            response_parts = []
            async for message in query(prompt=contextual_prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_parts.append(block.text)
                            if self.debug_mode:
                                print(f"[DEBUG] Received text block: {block.text[:100]}...")

            # Combine all response parts
            full_response = '\n'.join(response_parts)

            if self.debug_mode:
                print(f"[DEBUG] Full Claude response: {full_response}")

            # Process the response
            if full_response:
                # Add to conversation history
                self.conversation_history.append({
                    'input': user_input,
                    'response': full_response,
                    'timestamp': time.time()
                })

                # Cache the response
                if self.cache is not None:
                    cache_key = f"{user_input.lower().strip()}:{context.get('cwd', '')}"
                    self.cache[cache_key] = full_response

                return 'sdk_response', {
                    'response': full_response,
                    'original_input': user_input,
                    'context': context
                }
            else:
                return 'empty_response', {'error': 'Claude SDK returned empty response'}

        except CLINotFoundError:
            return 'cli_not_found', {
                'error': 'Claude Code CLI not found. Please install: npm install -g @anthropic-ai/claude-code'
            }
        except CLIConnectionError:
            return 'connection_error', {
                'error': 'Could not connect to Claude Code. Please check authentication: claude-code auth'
            }
        except ProcessError as e:
            return 'process_error', {
                'error': f'Claude Code process failed: {e}',
                'exit_code': getattr(e, 'exit_code', None)
            }
        except CLIJSONDecodeError as e:
            return 'json_error', {
                'error': f'Failed to parse Claude Code response: {e}'
            }
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] SDK exception: {e}")
            return 'sdk_error', {'error': f'SDK error: {str(e)}'}

    def parse_with_sdk(self, input_text: str, context: Dict[str, Any] = {}) -> Tuple[str, Dict[str, Any]]:
        """
        Use Claude Code SDK to interpret natural language into responses

        Returns:
            Tuple of (intent, parameters)
        """
        if not self.sdk_available:
            return 'sdk_not_available', {
                'error': 'Claude Code SDK is not installed or not accessible'
            }

        # Check cache first
        if self.cache is not None:
            cache_key = f"{input_text.lower().strip()}:{context.get('cwd', '')}"
            if cache_key in self.cache:
                cached_response = self.cache[cache_key]
                return 'sdk_response', {
                    'response': cached_response,
                    'original_input': input_text,
                    'from_cache': True
                }

        try:
            # Run the async query in a synchronous context
            return anyio.run(self._query_claude_sdk, input_text, context)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error running async query: {e}")
            return 'sdk_error', {'error': f'Failed to execute SDK query: {str(e)}'}

    def parse(self, input_text: str, context: Dict[str, Any] = {}) -> Tuple[str, Dict[str, Any]]:
        """
        Main parse method that uses Claude Code SDK

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

        # Validate and sanitize context
        validated_context = self._validate_context(context)

        # Check SDK availability and provide specific guidance
        if not SDK_AVAILABLE:
            return 'sdk_not_available', {
                'error': 'Claude Code SDK Python module is not installed',
                'input': sanitized_input,
                'help': 'Install with: pip install claude-code-sdk anyio'
            }

        if not self._check_claude_code():
            return 'cli_not_available', {
                'error': 'Claude Code CLI is not installed or not authenticated',
                'input': sanitized_input,
                'help': """To use Claude Code SDK, you need the Claude Code CLI:

1. Install Claude Code CLI:
   npm install -g @anthropic-ai/claude-code

2. Authenticate with your Claude.ai account:
   claude-code auth

3. This will open a browser for authentication

Note: The SDK uses the CLI for communication with Claude"""
            }

        if not self.sdk_available:
            return 'sdk_not_available', {
                'error': 'Claude Code SDK is not properly configured',
                'input': sanitized_input,
                'help': 'Check that both the SDK and CLI are installed'
            }

        return self.parse_with_sdk(sanitized_input, validated_context)

    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get command suggestions based on partial input and history"""
        # Input validation
        if not partial_input or not isinstance(partial_input, str):
            return []

        # Sanitize input for safety
        safe_input = self._sanitize_input(partial_input.strip())
        if not safe_input:
            return []

        suggestions = []
        partial_lower = safe_input.lower()

        # Context-aware suggestions based on common VibeOS tasks
        if partial_lower.startswith('create'):
            suggestions.extend([
                'create a new Python project with testing framework',
                'create a React app with authentication',
                'create a REST API with database integration',
                'create a machine learning environment'
            ])
        elif partial_lower.startswith('install'):
            suggestions.extend([
                'install everything I need for web development',
                'install machine learning libraries',
                'install development tools and configure them',
                'install and configure Docker'
            ])
        elif partial_lower.startswith('set'):
            suggestions.extend([
                'set up a complete development environment for Python',
                'set up CI/CD pipeline for my project',
                'set up database and connect it to my app',
                'set up testing and code quality tools'
            ])
        elif partial_lower.startswith('fix'):
            suggestions.extend([
                'fix all the errors in my code',
                'fix import and dependency issues',
                'fix my Git repository configuration',
                'fix performance issues in my application'
            ])
        elif partial_lower.startswith('deploy'):
            suggestions.extend([
                'deploy my application to production',
                'deploy using Docker containers',
                'deploy to cloud infrastructure',
                'deploy with automatic scaling'
            ])

        # Add suggestions from conversation history
        for item in self.conversation_history[-5:]:
            if partial_lower in item['input'].lower():
                suggestions.append(item['input'])

        return suggestions[:5]

    def clear_context(self) -> None:
        """Clear conversation history and cache using shared context manager."""
        self.context_manager.clear_context()

    @property
    def claude_available(self) -> bool:
        """Compatibility property for existing code"""
        return self.sdk_available

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the SDK parser"""
        return {
            'sdk_available': self.sdk_available,
            'sdk_imported': SDK_AVAILABLE,
            'cli_available': self._check_claude_code(),
            'conversation_items': len(self.conversation_history),
            'cache_items': len(self.cache) if self.cache else 0,
            'debug_mode': self.debug_mode
        }