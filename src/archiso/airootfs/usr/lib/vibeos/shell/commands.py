#!/usr/bin/env python3
"""
Command Executor for VibeOS Shell
Executes parsed intents as system commands
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


class CommandExecutor:
    """Execute parsed natural language commands"""
    
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load project templates"""
        return {
            'python_gitignore': """__pycache__/
*.py[cod]
*$py.class
*.so
.env
venv/
env/
.venv/
.pytest_cache/
.coverage
*.egg-info/
dist/
build/
""",
            'node_gitignore': """node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.env
.env.local
dist/
build/
.DS_Store
""",
            'python_main': """#!/usr/bin/env python3
\"\"\"
{name} - A Python project
\"\"\"

def main():
    print("Welcome to {name}!")
    
if __name__ == "__main__":
    main()
""",
            'node_package': """{
  "name": "{name}",
  "version": "1.0.0",
  "description": "A Node.js project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "MIT"
}
""",
        }
    
    def execute(self, intent: str, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Execute a command based on intent and parameters"""
        
        # Map intents to executor methods
        executors = {
            'create_project': self._create_project,
            'install_package': self._install_package,
            'search_package': self._search_package,
            'git_status': self._git_status,
            'git_commit': self._git_commit,
            'git_push': self._git_push,
            'git_pull': self._git_pull,
            'git_init': self._git_init,
            'run_tests': self._run_tests,
            'build_project': self._build_project,
            'start_dev_server': self._start_dev_server,
            'system_info': self._system_info,
            'disk_usage': self._disk_usage,
            'list_processes': self._list_processes,
            'change_directory': self._change_directory,
            'list_files': self._list_files,
            'show_pwd': self._show_pwd,
            'create_venv': self._create_venv,
            'activate_venv': self._activate_venv,
            'update_system': self._update_system,
        }
        
        if intent in executors:
            return executors[intent](params, context)
        
        return {'success': False, 'error': f'Unknown intent: {intent}'}
    
    def _run_command(self, cmd: list, capture_output: bool = True) -> Dict[str, Any]:
        """Run a shell command and return result"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout if capture_output else None
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr if capture_output else 'Command failed'
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_project(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Create a new project"""
        project_type = params.get('type', 'python')
        project_name = params.get('name', 'myproject')
        
        # Create project directory
        project_path = Path(project_name)
        if project_path.exists():
            return {'success': False, 'error': f'Directory {project_name} already exists'}
        
        try:
            project_path.mkdir()
            os.chdir(project_path)
            
            if project_type in ['python', 'py']:
                # Create Python project structure
                Path('src').mkdir()
                Path('tests').mkdir()
                Path('docs').mkdir()
                
                # Create main.py
                with open('src/main.py', 'w') as f:
                    f.write(self.templates['python_main'].format(name=project_name))
                
                # Create .gitignore
                with open('.gitignore', 'w') as f:
                    f.write(self.templates['python_gitignore'])
                
                # Create requirements.txt
                Path('requirements.txt').touch()
                
                # Create README.md
                with open('README.md', 'w') as f:
                    f.write(f"# {project_name}\n\nA Python project\n")
                
                return {
                    'success': True,
                    'output': f"✓ Created Python project '{project_name}'\n" +
                             f"  Structure:\n" +
                             f"    {project_name}/\n" +
                             f"    ├── src/main.py\n" +
                             f"    ├── tests/\n" +
                             f"    ├── docs/\n" +
                             f"    ├── requirements.txt\n" +
                             f"    ├── .gitignore\n" +
                             f"    └── README.md\n\n" +
                             f"  Next steps:\n" +
                             f"    • Create virtual environment: 'create virtual environment'\n" +
                             f"    • Initialize git: 'init git repository'"
                }
                
            elif project_type in ['node', 'nodejs', 'javascript', 'js']:
                # Create Node.js project structure
                Path('src').mkdir()
                Path('tests').mkdir()
                
                # Create package.json
                with open('package.json', 'w') as f:
                    f.write(self.templates['node_package'].format(name=project_name))
                
                # Create index.js
                with open('index.js', 'w') as f:
                    f.write(f'console.log("Welcome to {project_name}!");\n')
                
                # Create .gitignore
                with open('.gitignore', 'w') as f:
                    f.write(self.templates['node_gitignore'])
                
                # Create README.md
                with open('README.md', 'w') as f:
                    f.write(f"# {project_name}\n\nA Node.js project\n")
                
                return {
                    'success': True,
                    'output': f"✓ Created Node.js project '{project_name}'\n" +
                             f"  Structure:\n" +
                             f"    {project_name}/\n" +
                             f"    ├── index.js\n" +
                             f"    ├── src/\n" +
                             f"    ├── tests/\n" +
                             f"    ├── package.json\n" +
                             f"    ├── .gitignore\n" +
                             f"    └── README.md\n\n" +
                             f"  Next steps:\n" +
                             f"    • Install dependencies: 'install npm packages'\n" +
                             f"    • Initialize git: 'init git repository'"
                }
            
            elif project_type in ['react']:
                # For React, we'd normally use create-react-app
                return {
                    'success': True,
                    'output': f"To create a React project, I'll use create-react-app.\n" +
                             f"Run: npx create-react-app {project_name}"
                }
            
            else:
                # Generic project
                Path('src').mkdir()
                Path('docs').mkdir()
                
                with open('README.md', 'w') as f:
                    f.write(f"# {project_name}\n\nA new project\n")
                
                return {
                    'success': True,
                    'output': f"✓ Created project '{project_name}'\n" +
                             f"  Basic structure created in {project_name}/"
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Failed to create project: {e}'}
    
    def _install_package(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Install packages"""
        packages = params.get('packages', [])
        
        if not packages:
            return {'success': False, 'error': 'No packages specified'}
        
        # Detect package manager
        if Path('package.json').exists():
            # Node.js project - use npm
            cmd = ['npm', 'install'] + packages
            manager = 'npm'
        elif Path('requirements.txt').exists() or Path('setup.py').exists():
            # Python project - use pip
            cmd = ['pip', 'install'] + packages
            manager = 'pip'
        else:
            # System package - use pacman (Arch Linux)
            cmd = ['sudo', 'pacman', '-S', '--noconfirm'] + packages
            manager = 'pacman'
        
        print(f"Installing {', '.join(packages)} with {manager}...")
        result = self._run_command(cmd, capture_output=False)
        
        if result['success']:
            result['output'] = f"✓ Successfully installed: {', '.join(packages)}"
        
        return result
    
    def _search_package(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Search for packages"""
        query = params.get('query', '')
        
        if not query:
            return {'success': False, 'error': 'No search query specified'}
        
        # Search in Arch repositories
        cmd = ['pacman', '-Ss', query]
        result = self._run_command(cmd)
        
        if result['success']:
            lines = result['output'].split('\n')[:10]  # Show first 10 results
            result['output'] = f"Package search results for '{query}':\n" + '\n'.join(lines)
        
        return result
    
    def _git_status(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Show git status"""
        return self._run_command(['git', 'status'])
    
    def _git_commit(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Commit changes"""
        message = params.get('message', 'Update')
        
        # First add all changes
        add_result = self._run_command(['git', 'add', '.'])
        if not add_result['success']:
            return add_result
        
        # Then commit
        return self._run_command(['git', 'commit', '-m', message])
    
    def _git_push(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Push to remote"""
        return self._run_command(['git', 'push'])
    
    def _git_pull(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Pull from remote"""
        return self._run_command(['git', 'pull'])
    
    def _git_init(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Initialize git repository"""
        result = self._run_command(['git', 'init'])
        if result['success']:
            result['output'] = "✓ Initialized git repository\n" + result.get('output', '')
        return result
    
    def _run_tests(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Run project tests"""
        # Detect test runner
        if Path('package.json').exists():
            return self._run_command(['npm', 'test'], capture_output=False)
        elif Path('pytest.ini').exists() or Path('tests').exists():
            return self._run_command(['pytest'], capture_output=False)
        else:
            return {'success': False, 'error': 'No test configuration found'}
    
    def _build_project(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Build the project"""
        if Path('package.json').exists():
            return self._run_command(['npm', 'run', 'build'], capture_output=False)
        elif Path('Makefile').exists():
            return self._run_command(['make'], capture_output=False)
        else:
            return {'success': False, 'error': 'No build configuration found'}
    
    def _start_dev_server(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Start development server"""
        if Path('package.json').exists():
            return self._run_command(['npm', 'start'], capture_output=False)
        elif Path('manage.py').exists():
            return self._run_command(['python', 'manage.py', 'runserver'], capture_output=False)
        else:
            return {'success': False, 'error': 'No development server configuration found'}
    
    def _system_info(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Show system information"""
        cmd = ['uname', '-a']
        result = self._run_command(cmd)
        
        if result['success']:
            # Add more system info
            cpu_info = subprocess.run(['lscpu'], capture_output=True, text=True)
            mem_info = subprocess.run(['free', '-h'], capture_output=True, text=True)
            
            output = "System Information:\n"
            output += "─" * 40 + "\n"
            output += result['output'] + "\n"
            
            if cpu_info.returncode == 0:
                cpu_lines = cpu_info.stdout.split('\n')[:5]
                output += "\nCPU:\n" + '\n'.join(cpu_lines) + "\n"
            
            if mem_info.returncode == 0:
                output += "\nMemory:\n" + mem_info.stdout
            
            result['output'] = output
        
        return result
    
    def _disk_usage(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Show disk usage"""
        return self._run_command(['df', '-h'])
    
    def _list_processes(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """List running processes"""
        return self._run_command(['ps', 'aux', '--sort=-pcpu', '|', 'head', '-20'])
    
    def _change_directory(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Change directory"""
        path = params.get('path', '~')
        path = os.path.expanduser(path)
        
        try:
            os.chdir(path)
            return {'success': True, 'output': f"Changed to: {os.getcwd()}"}
        except FileNotFoundError:
            return {'success': False, 'error': f"Directory not found: {path}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _list_files(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """List files in current directory"""
        return self._run_command(['ls', '-la'])
    
    def _show_pwd(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Show current directory"""
        return {'success': True, 'output': os.getcwd()}
    
    def _create_venv(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Create Python virtual environment"""
        result = self._run_command(['python', '-m', 'venv', 'venv'])
        if result['success']:
            result['output'] = "✓ Created virtual environment in ./venv\n" + \
                              "  Activate with: 'activate virtual environment'"
        return result
    
    def _activate_venv(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Activate virtual environment"""
        # Note: This is tricky in a subprocess, providing instructions instead
        return {
            'success': True,
            'output': "To activate the virtual environment, run:\n" +
                     "  source venv/bin/activate"
        }
    
    def _update_system(self, params: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Update system packages"""
        print("Updating system packages...")
        return self._run_command(['sudo', 'pacman', '-Syu', '--noconfirm'], capture_output=False)