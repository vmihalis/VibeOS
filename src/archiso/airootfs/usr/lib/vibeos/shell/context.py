#!/usr/bin/env python3
"""
Context Manager for VibeOS Shell
Tracks current project context and developer workflow state
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class ContextManager:
    """Manage shell context and maintain flow state"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'vibeos'
        self.config_file = self.config_dir / 'context.json'
        self.history_file = self.config_dir / 'command_history.json'
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize context
        self.context = self._load_context()
        self.command_history = self._load_history()
        
    def _load_context(self) -> Dict[str, Any]:
        """Load saved context or create new one"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default context
        return {
            'current_project': None,
            'project_type': None,
            'recent_commands': [],
            'preferences': {
                'editor': os.environ.get('EDITOR', 'vim'),
                'shell': os.environ.get('SHELL', '/bin/bash'),
                'package_manager': 'auto',  # auto-detect
            },
            'environment': {
                'virtual_env': None,
                'node_version': None,
                'python_version': None,
            }
        }
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load command history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save(self):
        """Save context to disk"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.context, f, indent=2)
            
            # Keep only last 1000 history entries
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]
            
            with open(self.history_file, 'w') as f:
                json.dump(self.command_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save context: {e}")
    
    def detect_project(self) -> Dict[str, Any]:
        """Detect current project type and configuration"""
        cwd = Path.cwd()
        project_info = {
            'path': str(cwd),
            'name': cwd.name,
            'type': 'unknown',
            'has_git': False,
            'has_venv': False,
            'config_files': []
        }
        
        # Check for Git
        if (cwd / '.git').exists():
            project_info['has_git'] = True
            
            # Get current branch
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    project_info['git_branch'] = result.stdout.strip()
            except:
                pass
        
        # Detect project type by config files
        if (cwd / 'package.json').exists():
            project_info['type'] = 'node'
            project_info['config_files'].append('package.json')
            
            # Check for specific frameworks
            try:
                with open(cwd / 'package.json', 'r') as f:
                    pkg = json.load(f)
                    deps = pkg.get('dependencies', {})
                    dev_deps = pkg.get('devDependencies', {})
                    all_deps = {**deps, **dev_deps}
                    
                    if 'react' in all_deps:
                        project_info['framework'] = 'react'
                    elif 'vue' in all_deps:
                        project_info['framework'] = 'vue'
                    elif 'angular' in all_deps:
                        project_info['framework'] = 'angular'
                    elif 'express' in all_deps:
                        project_info['framework'] = 'express'
            except:
                pass
        
        elif (cwd / 'requirements.txt').exists() or (cwd / 'setup.py').exists():
            project_info['type'] = 'python'
            if (cwd / 'requirements.txt').exists():
                project_info['config_files'].append('requirements.txt')
            if (cwd / 'setup.py').exists():
                project_info['config_files'].append('setup.py')
            
            # Check for virtual environment
            for venv_dir in ['venv', 'env', '.venv']:
                if (cwd / venv_dir).exists():
                    project_info['has_venv'] = True
                    project_info['venv_path'] = str(cwd / venv_dir)
                    break
            
            # Check for specific frameworks
            if (cwd / 'manage.py').exists():
                project_info['framework'] = 'django'
            elif (cwd / 'app.py').exists() or (cwd / 'application.py').exists():
                # Could be Flask
                project_info['framework'] = 'flask'
        
        elif (cwd / 'Cargo.toml').exists():
            project_info['type'] = 'rust'
            project_info['config_files'].append('Cargo.toml')
        
        elif (cwd / 'go.mod').exists():
            project_info['type'] = 'go'
            project_info['config_files'].append('go.mod')
        
        elif (cwd / 'Makefile').exists():
            project_info['type'] = 'make'
            project_info['config_files'].append('Makefile')
        
        return project_info
    
    def update_current_project(self):
        """Update current project context"""
        project_info = self.detect_project()
        self.context['current_project'] = project_info['path']
        self.context['project_type'] = project_info['type']
        
        # Store additional project info
        self.context['project_info'] = project_info
        self.save()
    
    def add_command(self, command: str, intent: str, success: bool):
        """Add command to history"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'intent': intent,
            'success': success,
            'directory': os.getcwd()
        }
        
        self.command_history.append(entry)
        
        # Update recent commands in context
        self.context['recent_commands'].append(command)
        if len(self.context['recent_commands']) > 10:
            self.context['recent_commands'] = self.context['recent_commands'][-10:]
        
        self.save()
    
    def get_suggestions(self) -> List[str]:
        """Get contextual suggestions based on current project"""
        suggestions = []
        project_info = self.detect_project()
        
        if project_info['type'] == 'python':
            if not project_info['has_venv']:
                suggestions.append("create virtual environment")
            if not project_info['has_git']:
                suggestions.append("initialize git repository")
            suggestions.extend([
                "install pytest",
                "run tests",
                "format code with black"
            ])
        
        elif project_info['type'] == 'node':
            if not project_info['has_git']:
                suggestions.append("initialize git repository")
            suggestions.extend([
                "install dependencies",
                "run development server",
                "build for production"
            ])
        
        elif project_info['type'] == 'unknown':
            suggestions.extend([
                "create new python project",
                "create new node project",
                "initialize git repository"
            ])
        
        return suggestions
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information"""
        env_info = {}
        
        # Python version
        try:
            result = subprocess.run(
                ['python', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                env_info['python'] = result.stdout.strip()
        except:
            pass
        
        # Node version
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                env_info['node'] = result.stdout.strip()
        except:
            pass
        
        # Check for active virtual environment
        if 'VIRTUAL_ENV' in os.environ:
            env_info['virtual_env'] = os.environ['VIRTUAL_ENV']
        
        return env_info