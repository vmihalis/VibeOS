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

    def __init__(self):
        self.config = self._load_config()
        self.debug_mode = self._is_debug_enabled()

        if self.debug_mode:
            print("[DEBUG] Initializing Claude SDK Parser...")
            print(f"[DEBUG] SDK Available: {SDK_AVAILABLE}")

        # SDK requires both the Python module AND the CLI to be available
        self.sdk_available = SDK_AVAILABLE and self._check_claude_code()
        self.context_file = Path("/tmp/.vibeos_claude_context.json")
        self.conversation_history = []
        self.cache = {} if self.config.get('claude_code', {}).get('cache_commands', True) else None

        if self.debug_mode:
            print(f"[DEBUG] Claude SDK available: {self.sdk_available}")
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
                'fallback_to_regex': False,
                'command_timeout': 30,
                'max_turns': 3,
                'cache_commands': True
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

    def _sanitize_input(self, text: str) -> str:
        """Simple input sanitization"""
        if not text or not isinstance(text, str):
            return ""

        # Basic cleanup
        text = text.strip()
        if len(text) > 5000:  # Reasonable limit
            text = text[:5000]

        return text

    def parse(self, input_text: str, context: Dict[str, Any] = {}) -> Tuple[str, Dict[str, Any]]:
        """Main parse method that uses Claude Code SDK"""
        # Basic input validation
        if not input_text or not isinstance(input_text, str):
            return 'input_error', {'error': 'Input must be a non-empty string'}

        sanitized_input = self._sanitize_input(input_text)
        if not sanitized_input:
            return 'input_error', {'error': 'Empty input'}

        # Simple context validation
        if not isinstance(context, dict):
            context = {}
        if 'cwd' not in context:
            context['cwd'] = os.getcwd()

        # Check SDK availability
        if not self.sdk_available:
            return 'sdk_not_available', {
                'error': 'Claude Code is not installed or not authenticated',
                'help': 'Run: vibeos-install-claude'
            }

        return self.parse_with_sdk(sanitized_input, context)

    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get command suggestions based on partial input"""
        if not partial_input:
            return []

        partial_lower = partial_input.lower()
        suggestions = []

        # Simple pattern matching
        if partial_lower.startswith('create'):
            suggestions = ['create a new Python project', 'create a React app']
        elif partial_lower.startswith('install'):
            suggestions = ['install development tools', 'install claude']
        elif partial_lower.startswith('fix'):
            suggestions = ['fix errors in my code', 'fix dependencies']

        return suggestions[:3]

    def clear_context(self) -> None:
        """Clear conversation history and cache."""
        self.conversation_history.clear()
        if self.cache:
            self.cache.clear()

        if self.context_file.exists():
            try:
                self.context_file.unlink()
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not remove context file: {e}")

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