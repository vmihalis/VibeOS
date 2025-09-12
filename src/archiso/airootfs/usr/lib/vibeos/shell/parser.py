#!/usr/bin/env python3
"""
Natural Language Parser for VibeOS Shell
Converts natural language input into structured commands
"""

import re
from typing import Tuple, Dict, Any, List


class NaturalLanguageParser:
    """Parse natural language input into executable intents"""
    
    def __init__(self):
        # Define patterns for common developer commands
        self.patterns = {
            # Project creation
            'create_project': [
                r'create\s+(?:a\s+)?new\s+(\w+)\s+project\s+(?:called\s+|named\s+)?([a-zA-Z0-9_-]+)',
                r'start\s+(?:a\s+)?new\s+(\w+)\s+project\s+([a-zA-Z0-9_-]+)',
                r'init\s+(\w+)\s+project\s+([a-zA-Z0-9_-]+)',
            ],
            
            # Package management
            'install_package': [
                r'install\s+([\w\-\./]+(?:\s+[\w\-\./]+)*)',
                r'add\s+([\w\-\./]+(?:\s+[\w\-\./]+)*)',
                r'get\s+([\w\-\./]+(?:\s+[\w\-\./]+)*)',
            ],
            
            'search_package': [
                r'search\s+(?:for\s+)?([\w\-]+)',
                r'find\s+package\s+([\w\-]+)',
                r'look\s+for\s+([\w\-]+)',
            ],
            
            # Git operations
            'git_status': [
                r'git\s+status',
                r'show\s+git\s+status',
                r'what\'?s?\s+changed',
                r'show\s+changes',
            ],
            
            'git_commit': [
                r'commit\s+(?:changes\s+)?(?:with\s+message\s+)?["\'](.+)["\']',
                r'git\s+commit\s+["\'](.+)["\']',
                r'save\s+changes\s+["\'](.+)["\']',
            ],
            
            'git_push': [
                r'push\s+(?:to\s+)?(?:remote)?',
                r'git\s+push',
                r'upload\s+changes',
            ],
            
            'git_pull': [
                r'pull\s+(?:from\s+)?(?:remote)?',
                r'git\s+pull',
                r'update\s+from\s+remote',
            ],
            
            'git_init': [
                r'init(?:ialize)?\s+git(?:\s+repo(?:sitory)?)?',
                r'create\s+git\s+repo(?:sitory)?',
                r'start\s+version\s+control',
            ],
            
            # Development commands
            'run_tests': [
                r'run\s+tests?',
                r'test\s+(?:the\s+)?(?:project|code)',
                r'execute\s+tests?',
            ],
            
            'build_project': [
                r'build\s+(?:the\s+)?project',
                r'compile\s+(?:the\s+)?(?:project|code)',
                r'make\s+(?:the\s+)?project',
            ],
            
            'start_dev_server': [
                r'start\s+(?:dev(?:elopment)?\s+)?server',
                r'run\s+(?:dev(?:elopment)?\s+)?server',
                r'launch\s+(?:dev(?:elopment)?\s+)?server',
            ],
            
            # System information
            'system_info': [
                r'show\s+system\s+(?:info(?:rmation)?|status)',
                r'system\s+(?:info(?:rmation)?|status)',
                r'what\'?s?\s+(?:the\s+)?system\s+status',
            ],
            
            'disk_usage': [
                r'(?:show\s+)?disk\s+(?:usage|space)',
                r'how\s+much\s+(?:disk\s+)?space',
                r'check\s+storage',
            ],
            
            'list_processes': [
                r'(?:show\s+|list\s+)?(?:running\s+)?processes',
                r'what\'?s?\s+running',
                r'show\s+tasks',
            ],
            
            # Navigation
            'change_directory': [
                r'(?:go\s+to|cd\s+to?|change\s+to|navigate\s+to)\s+(.+)',
                r'enter\s+(.+)\s+(?:directory|folder)',
            ],
            
            'list_files': [
                r'(?:list|show|ls)\s+(?:files?|directory|folder)?',
                r'what\'?s?\s+(?:in\s+)?(?:here|this\s+(?:directory|folder))',
            ],
            
            'show_pwd': [
                r'(?:show\s+)?(?:current\s+)?(?:directory|folder|pwd|path)',
                r'where\s+am\s+i',
            ],
            
            # Virtual environment
            'create_venv': [
                r'create\s+(?:a\s+)?(?:virtual\s+)?env(?:ironment)?',
                r'make\s+(?:a\s+)?venv',
                r'setup\s+(?:virtual\s+)?env(?:ironment)?',
            ],
            
            'activate_venv': [
                r'activate\s+(?:virtual\s+)?env(?:ironment)?',
                r'enter\s+(?:virtual\s+)?env(?:ironment)?',
                r'use\s+venv',
            ],
            
            # Update system
            'update_system': [
                r'update\s+(?:the\s+)?system',
                r'upgrade\s+(?:system\s+)?packages',
                r'system\s+update',
            ],
        }
        
    def parse(self, input_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse natural language input into intent and parameters
        
        Returns:
            Tuple of (intent, parameters)
        """
        input_lower = input_text.lower().strip()
        
        # Check each pattern category
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.match(pattern, input_lower)
                if match:
                    return self._extract_params(intent, match)
        
        # If no pattern matches, try to extract some basic intent
        return self._fallback_parse(input_text)
    
    def _extract_params(self, intent: str, match: re.Match) -> Tuple[str, Dict[str, Any]]:
        """Extract parameters from regex match"""
        params = {}
        
        if intent == 'create_project':
            params['type'] = match.group(1)
            params['name'] = match.group(2)
            
        elif intent == 'install_package':
            packages = match.group(1).split()
            params['packages'] = packages
            
        elif intent == 'search_package':
            params['query'] = match.group(1)
            
        elif intent == 'git_commit':
            params['message'] = match.group(1)
            
        elif intent == 'change_directory':
            params['path'] = match.group(1)
            
        # For intents without parameters, just return empty dict
        
        return intent, params
    
    def _fallback_parse(self, input_text: str) -> Tuple[str, Dict[str, Any]]:
        """Fallback parsing for unrecognized commands"""
        input_lower = input_text.lower()
        
        # Try to detect some keywords
        if any(word in input_lower for word in ['create', 'new', 'make']):
            return 'suggest_create', {'query': input_text}
        elif any(word in input_lower for word in ['install', 'add', 'get']):
            return 'suggest_install', {'query': input_text}
        elif 'git' in input_lower:
            return 'suggest_git', {'query': input_text}
        elif any(word in input_lower for word in ['show', 'list', 'display']):
            return 'suggest_show', {'query': input_text}
        
        return 'unknown', {'query': input_text}
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        partial_lower = partial_input.lower()
        
        # Common command starters
        starters = {
            'create': ['create a new python project', 'create a new react app', 'create virtual environment'],
            'install': ['install nodejs', 'install python package', 'install docker'],
            'show': ['show system info', 'show git status', 'show disk usage'],
            'git': ['git status', 'git commit "message"', 'git push'],
            'run': ['run tests', 'run development server', 'run build'],
        }
        
        for starter, examples in starters.items():
            if partial_lower.startswith(starter):
                suggestions.extend(examples)
        
        return suggestions[:5]  # Return top 5 suggestions