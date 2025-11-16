"""
MCP Server for File System Operations
Provides tools for reading, searching, and analyzing code files
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import fnmatch


class FileSystemMCP:
    """MCP Server for filesystem operations"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.allowed_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.php', '.rb', '.cs', '.swift', '.kt', '.scala',
            '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.xml', '.html', '.css'
        }

    def list_files(self, pattern: str = "*") -> List[Dict[str, Any]]:
        """List all files matching pattern in repository"""
        files = []

        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'dist', 'build']]

            for filename in filenames:
                if fnmatch.fnmatch(filename, pattern):
                    file_path = Path(root) / filename
                    rel_path = file_path.relative_to(self.repo_path)

                    if file_path.suffix in self.allowed_extensions:
                        try:
                            stat = file_path.stat()
                            files.append({
                                'path': str(rel_path),
                                'size': stat.st_size,
                                'extension': file_path.suffix,
                                'name': filename
                            })
                        except Exception:
                            continue

        return files

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read content of a specific file"""
        full_path = self.repo_path / file_path

        if not full_path.exists():
            return {'error': f'File not found: {file_path}'}

        if not full_path.is_relative_to(self.repo_path):
            return {'error': 'Access denied: Path outside repository'}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'path': file_path,
                'content': content,
                'lines': len(content.splitlines()),
                'size': len(content)
            }
        except UnicodeDecodeError:
            return {'error': 'Binary file or encoding issue'}
        except Exception as e:
            return {'error': str(e)}

    def search_in_files(self, query: str, file_pattern: str = "*.py") -> List[Dict[str, Any]]:
        """Search for text across files"""
        results = []
        files = self.list_files(file_pattern)

        for file_info in files:
            file_data = self.read_file(file_info['path'])
            if 'content' in file_data:
                lines = file_data['content'].splitlines()
                for line_num, line in enumerate(lines, 1):
                    if query.lower() in line.lower():
                        results.append({
                            'file': file_info['path'],
                            'line': line_num,
                            'content': line.strip(),
                            'context': self._get_context(lines, line_num)
                        })

        return results

    def get_file_structure(self) -> Dict[str, Any]:
        """Get directory tree structure"""
        def build_tree(path: Path, max_depth: int = 3, current_depth: int = 0):
            if current_depth >= max_depth:
                return None

            tree = {'name': path.name, 'type': 'directory', 'children': []}

            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                for item in items:
                    if item.name.startswith('.') or item.name in ['node_modules', 'venv', '__pycache__']:
                        continue

                    if item.is_file() and item.suffix in self.allowed_extensions:
                        tree['children'].append({
                            'name': item.name,
                            'type': 'file',
                            'extension': item.suffix
                        })
                    elif item.is_dir():
                        subtree = build_tree(item, max_depth, current_depth + 1)
                        if subtree and subtree['children']:
                            tree['children'].append(subtree)
            except PermissionError:
                pass

            return tree

        return build_tree(self.repo_path)

    def _get_context(self, lines: List[str], line_num: int, context_size: int = 2) -> List[str]:
        """Get surrounding lines for context"""
        start = max(0, line_num - context_size - 1)
        end = min(len(lines), line_num + context_size)
        return lines[start:end]

    def analyze_imports(self, file_path: str) -> List[str]:
        """Extract import statements from a Python file"""
        file_data = self.read_file(file_path)
        if 'content' not in file_data:
            return []

        imports = []
        for line in file_data['content'].splitlines():
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)

        return imports
