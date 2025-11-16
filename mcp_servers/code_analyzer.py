"""
MCP Server for Code Analysis
Provides tools for analyzing code quality, complexity, and patterns
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit


class CodeAnalyzerMCP:
    """MCP Server for code analysis operations"""

    def __init__(self):
        self.language_patterns = {
            'python': {
                'function': r'def\s+(\w+)\s*\(',
                'class': r'class\s+(\w+)',
                'import': r'^(?:from\s+[\w.]+\s+)?import\s+.+',
            },
            'javascript': {
                'function': r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()',
                'class': r'class\s+(\w+)',
                'import': r'^import\s+.+',
            }
        }

    def analyze_python_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Python file for various metrics"""
        try:
            tree = ast.parse(content)

            analysis = {
                'file': file_path,
                'language': 'python',
                'metrics': {},
                'functions': [],
                'classes': [],
                'imports': [],
                'issues': []
            }

            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': len(node.args.args),
                        'decorators': len(node.decorator_list)
                    })
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis['imports'].append(alias.name)
                    else:
                        analysis['imports'].append(node.module or '')

            # Complexity analysis
            try:
                complexity = cc_visit(content)
                analysis['metrics']['complexity'] = [
                    {
                        'name': item.name,
                        'complexity': item.complexity,
                        'line': item.lineno
                    }
                    for item in complexity
                ]
            except Exception:
                pass

            # Maintainability Index
            try:
                mi_score = mi_visit(content, multi=True)
                analysis['metrics']['maintainability_index'] = mi_score
            except Exception:
                pass

            # Basic issues detection
            analysis['issues'] = self._detect_python_issues(content)

            return analysis

        except SyntaxError as e:
            return {
                'file': file_path,
                'error': f'Syntax error: {str(e)}',
                'line': e.lineno
            }
        except Exception as e:
            return {
                'file': file_path,
                'error': str(e)
            }

    def _detect_python_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect common Python issues"""
        issues = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for common issues
            if 'eval(' in line:
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'line': line_num,
                    'message': 'Use of eval() is dangerous',
                    'suggestion': 'Consider using ast.literal_eval() or safer alternatives'
                })

            if 'exec(' in line:
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'line': line_num,
                    'message': 'Use of exec() is dangerous',
                    'suggestion': 'Avoid dynamic code execution'
                })

            if re.search(r'password\s*=\s*["\']', line, re.IGNORECASE):
                issues.append({
                    'type': 'security',
                    'severity': 'critical',
                    'line': line_num,
                    'message': 'Hardcoded password detected',
                    'suggestion': 'Use environment variables or secure secret management'
                })

            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    'type': 'maintenance',
                    'severity': 'low',
                    'line': line_num,
                    'message': 'TODO/FIXME comment found',
                    'suggestion': 'Address this comment or create a ticket'
                })

            if len(line) > 120:
                issues.append({
                    'type': 'style',
                    'severity': 'low',
                    'line': line_num,
                    'message': f'Line too long ({len(line)} characters)',
                    'suggestion': 'Break into multiple lines (PEP 8 recommends max 79-120)'
                })

        return issues

    def find_functions(self, content: str, language: str = 'python') -> List[Dict[str, Any]]:
        """Find all function definitions in code"""
        functions = []

        if language == 'python':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get docstring if available
                        docstring = ast.get_docstring(node)
                        functions.append({
                            'name': node.name,
                            'line': node.lineno,
                            'args': [arg.arg for arg in node.args.args],
                            'docstring': docstring[:100] if docstring else None,
                            'is_async': isinstance(node, ast.AsyncFunctionDef)
                        })
            except Exception:
                pass

        else:
            # Regex fallback for other languages
            pattern = self.language_patterns.get(language, {}).get('function')
            if pattern:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    functions.append({
                        'name': match.group(1),
                        'line': content[:match.start()].count('\n') + 1
                    })

        return functions

    def find_classes(self, content: str, language: str = 'python') -> List[Dict[str, Any]]:
        """Find all class definitions in code"""
        classes = []

        if language == 'python':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        docstring = ast.get_docstring(node)
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        classes.append({
                            'name': node.name,
                            'line': node.lineno,
                            'methods': methods,
                            'docstring': docstring[:100] if docstring else None,
                            'bases': [b.id for b in node.bases if isinstance(b, ast.Name)]
                        })
            except Exception:
                pass

        return classes

    def calculate_metrics(self, content: str, language: str = 'python') -> Dict[str, Any]:
        """Calculate various code metrics"""
        lines = content.splitlines()

        metrics = {
            'total_lines': len(lines),
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0
        }

        if language == 'python':
            in_multiline_comment = False
            for line in lines:
                stripped = line.strip()

                if not stripped:
                    metrics['blank_lines'] += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    in_multiline_comment = not in_multiline_comment
                    metrics['comment_lines'] += 1
                elif in_multiline_comment:
                    metrics['comment_lines'] += 1
                elif stripped.startswith('#'):
                    metrics['comment_lines'] += 1
                else:
                    metrics['code_lines'] += 1

        return metrics

    def suggest_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []

        # Check complexity
        if 'complexity' in analysis.get('metrics', {}):
            high_complexity = [
                item for item in analysis['metrics']['complexity']
                if item['complexity'] > 10
            ]
            if high_complexity:
                suggestions.append(
                    f"⚠️ Found {len(high_complexity)} functions with high complexity (>10). "
                    f"Consider refactoring: {', '.join(item['name'] for item in high_complexity[:3])}"
                )

        # Check maintainability
        if 'maintainability_index' in analysis.get('metrics', {}):
            mi = analysis['metrics']['maintainability_index']
            if mi < 20:
                suggestions.append(
                    f"⚠️ Low maintainability index ({mi:.1f}). "
                    "Consider refactoring for better code quality."
                )

        # Check for missing docstrings
        functions_without_docs = [
            f for f in analysis.get('functions', [])
            if not f.get('docstring')
        ]
        if len(functions_without_docs) > 3:
            suggestions.append(
                f"📝 {len(functions_without_docs)} functions lack docstrings. "
                "Add documentation for better maintainability."
            )

        return suggestions
