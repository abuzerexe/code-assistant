"""
MCP Server for GitHub API Integration
Provides tools for fetching repository data, issues, PRs, etc.
"""

import os
from typing import List, Dict, Any, Optional
import requests
from github import Github, GithubException


class GitHubMCP:
    """MCP Server for GitHub operations"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.github = Github(self.token) if self.token else None
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}

    def get_repo_info(self, repo_url: str) -> Dict[str, Any]:
        """Get basic repository information"""
        try:
            # Parse owner/repo from URL
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]

            if self.github:
                repo_obj = self.github.get_repo(f"{owner}/{repo}")
                return {
                    'name': repo_obj.name,
                    'full_name': repo_obj.full_name,
                    'description': repo_obj.description,
                    'stars': repo_obj.stargazers_count,
                    'forks': repo_obj.forks_count,
                    'language': repo_obj.language,
                    'topics': repo_obj.get_topics(),
                    'default_branch': repo_obj.default_branch,
                    'url': repo_obj.html_url
                }
            else:
                # Fallback to public API
                url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'name': data['name'],
                        'full_name': data['full_name'],
                        'description': data.get('description'),
                        'stars': data['stargazers_count'],
                        'forks': data['forks_count'],
                        'language': data.get('language'),
                        'topics': data.get('topics', []),
                        'default_branch': data['default_branch'],
                        'url': data['html_url']
                    }
                else:
                    return {'error': f'Failed to fetch repo: {response.status_code}'}

        except Exception as e:
            return {'error': str(e)}

    def get_repo_structure(self, repo_url: str, path: str = "") -> List[Dict[str, Any]]:
        """Get repository file structure"""
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]

            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                contents = response.json()
                result = []
                for item in contents:
                    result.append({
                        'name': item['name'],
                        'path': item['path'],
                        'type': item['type'],
                        'size': item.get('size', 0),
                        'url': item.get('download_url')
                    })
                return result
            else:
                return [{'error': f'Failed to fetch contents: {response.status_code}'}]

        except Exception as e:
            return [{'error': str(e)}]

    def get_file_content(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """Get content of a specific file from GitHub"""
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]

            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                if data.get('download_url'):
                    content_response = requests.get(data['download_url'])
                    if content_response.status_code == 200:
                        return {
                            'path': file_path,
                            'content': content_response.text,
                            'size': data.get('size', 0)
                        }

            return {'error': f'Failed to fetch file: {response.status_code}'}

        except Exception as e:
            return {'error': str(e)}

    def search_code(self, query: str, repo_url: str) -> List[Dict[str, Any]]:
        """Search for code in repository"""
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]

            url = f"https://api.github.com/search/code?q={query}+repo:{owner}/{repo}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('items', [])[:10]:  # Limit to 10 results
                    results.append({
                        'name': item['name'],
                        'path': item['path'],
                        'url': item['html_url']
                    })
                return results
            else:
                return [{'error': f'Search failed: {response.status_code}'}]

        except Exception as e:
            return [{'error': str(e)}]

    def get_recent_commits(self, repo_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits from repository"""
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]

            url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page={limit}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                commits = response.json()
                result = []
                for commit in commits:
                    result.append({
                        'sha': commit['sha'][:7],
                        'message': commit['commit']['message'].split('\n')[0],
                        'author': commit['commit']['author']['name'],
                        'date': commit['commit']['author']['date']
                    })
                return result
            else:
                return [{'error': f'Failed to fetch commits: {response.status_code}'}]

        except Exception as e:
            return [{'error': str(e)}]

    def clone_repo_url(self, repo_url: str) -> str:
        """Convert GitHub URL to clone URL"""
        if repo_url.endswith('.git'):
            return repo_url
        return f"{repo_url.rstrip('/')}.git"
