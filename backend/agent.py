"""
LangGraph Agent for Code Analysis
Implements multi-step reasoning flow for code understanding and review
"""

import os
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
import operator

from mcp_servers.filesystem_server import FileSystemMCP
from mcp_servers.github_server import GitHubMCP
from mcp_servers.code_analyzer import CodeAnalyzerMCP


class AgentState(TypedDict):
    """State for the agent graph"""
    messages: Annotated[List, operator.add]
    repo_path: str
    github_url: str
    current_step: str
    analysis_results: Dict[str, Any]
    user_query: str


class CodeAssistantAgent:
    """LangGraph-based agent for code analysis and assistance"""

    def __init__(self, repo_path: str = None, github_url: str = None):
        self.repo_path = repo_path
        self.github_url = github_url

        # Initialize MCP servers
        self.fs_mcp = FileSystemMCP(repo_path) if repo_path else None
        self.github_mcp = GitHubMCP()
        self.analyzer_mcp = CodeAnalyzerMCP()

        # Initialize LLM
        provider = os.getenv('LLM_PROVIDER', 'openai')
        if provider == 'anthropic':
            self.llm = ChatAnthropic(
                model=os.getenv('LLM_MODEL', 'claude-3-sonnet-20240229'),
                temperature=0.1
            )
        elif provider == 'openrouter':
            # OpenRouter configuration
            self.llm = ChatOpenAI(
                model=os.getenv('LLM_MODEL', 'openai/gpt-4-turbo-preview'),
                openai_api_key=os.getenv('OPENROUTER_API_KEY'),
                openai_api_base='https://openrouter.ai/api/v1',
                temperature=0.1,
                model_kwargs={
                    'extra_headers': {
                        'HTTP-Referer': 'https://code-assistant.app',
                        'X-Title': 'Code Assistant AI'
                    }
                }
            )
        else:
            self.llm = ChatOpenAI(
                model=os.getenv('LLM_MODEL', 'gpt-4-turbo-preview'),
                temperature=0.1
            )

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("understand_query", self.understand_query)
        workflow.add_node("plan_search", self.plan_search)
        workflow.add_node("execute_search", self.execute_search)
        workflow.add_node("analyze_code", self.analyze_code)
        workflow.add_node("generate_response", self.generate_response)

        # Add edges
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "plan_search")
        workflow.add_edge("plan_search", "execute_search")
        workflow.add_edge("execute_search", "analyze_code")
        workflow.add_edge("analyze_code", "generate_response")
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def understand_query(self, state: AgentState) -> AgentState:
        """Step 1: Understand the user's query and intent"""
        user_query = state['user_query']

        system_prompt = """You are a code analysis expert. Analyze the user's query and determine:
1. What type of request is this? (explanation, bug finding, review, documentation, refactoring)
2. What specific files or patterns should be searched?
3. What depth of analysis is needed?

Respond in JSON format with: {"intent": "...", "scope": "...", "depth": "..."}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]

        response = self.llm.invoke(messages)

        state['current_step'] = "Understanding query"
        state['messages'].append(AIMessage(content=f"🔍 Analyzing your question: {user_query}"))

        return state

    def plan_search(self, state: AgentState) -> AgentState:
        """Step 2: Plan which files and patterns to search"""
        user_query = state['user_query']

        # Determine search strategy based on query
        search_plan = {
            'patterns': [],
            'keywords': [],
            'file_types': []
        }

        # Extract keywords from query
        if 'authentication' in user_query.lower() or 'auth' in user_query.lower():
            search_plan['keywords'] = ['auth', 'login', 'password', 'token']
            search_plan['patterns'] = ['*auth*.py', '*login*.py']

        elif 'database' in user_query.lower() or 'sql' in user_query.lower():
            search_plan['keywords'] = ['db', 'database', 'query', 'sql']
            search_plan['patterns'] = ['*db*.py', '*model*.py']

        elif 'api' in user_query.lower() or 'endpoint' in user_query.lower():
            search_plan['keywords'] = ['api', 'route', 'endpoint', '@app']
            search_plan['patterns'] = ['*api*.py', '*route*.py', '*views*.py']

        elif 'bug' in user_query.lower() or 'error' in user_query.lower():
            search_plan['keywords'] = ['error', 'exception', 'try', 'except']
            search_plan['file_types'] = ['.py', '.js']

        else:
            # General search
            search_plan['patterns'] = ['*.py', '*.js']

        state['analysis_results'] = {'search_plan': search_plan}
        state['current_step'] = "Planning search"
        state['messages'].append(
            AIMessage(content=f"📋 Planning to search: {', '.join(search_plan['patterns'][:3])}")
        )

        return state

    def execute_search(self, state: AgentState) -> AgentState:
        """Step 3: Execute the search across codebase"""
        search_plan = state['analysis_results']['search_plan']
        results = {
            'files': [],
            'matches': []
        }

        if self.fs_mcp:
            # Search files
            for pattern in search_plan['patterns'][:5]:  # Limit patterns
                files = self.fs_mcp.list_files(pattern)
                results['files'].extend(files[:10])  # Limit results

            # Search for keywords
            for keyword in search_plan['keywords'][:3]:
                matches = self.fs_mcp.search_in_files(keyword, '*.py')
                results['matches'].extend(matches[:20])

            # Get file structure
            if not results['files']:
                results['structure'] = self.fs_mcp.get_file_structure()

        elif self.github_url:
            # Search GitHub repo
            repo_info = self.github_mcp.get_repo_info(self.github_url)
            results['repo_info'] = repo_info

            for keyword in search_plan['keywords'][:3]:
                matches = self.github_mcp.search_code(keyword, self.github_url)
                results['matches'].extend(matches)

        state['analysis_results']['search_results'] = results
        state['current_step'] = "Executing search"

        files_found = len(results['files'])
        matches_found = len(results['matches'])
        state['messages'].append(
            AIMessage(content=f"📁 Found {files_found} files, {matches_found} code matches")
        )

        return state

    def analyze_code(self, state: AgentState) -> AgentState:
        """Step 4: Analyze found code for insights"""
        search_results = state['analysis_results']['search_results']
        analysis = {
            'file_analyses': [],
            'issues': [],
            'suggestions': []
        }

        # Analyze top files
        if self.fs_mcp:
            for file_info in search_results.get('files', [])[:5]:
                file_data = self.fs_mcp.read_file(file_info['path'])

                if 'content' in file_data and file_info['path'].endswith('.py'):
                    # Analyze Python file
                    file_analysis = self.analyzer_mcp.analyze_python_file(
                        file_data['content'],
                        file_info['path']
                    )
                    analysis['file_analyses'].append(file_analysis)

                    # Collect issues
                    if 'issues' in file_analysis:
                        analysis['issues'].extend(file_analysis['issues'])

                    # Get suggestions
                    suggestions = self.analyzer_mcp.suggest_improvements(file_analysis)
                    analysis['suggestions'].extend(suggestions)

        state['analysis_results']['code_analysis'] = analysis
        state['current_step'] = "Analyzing code"

        issues_count = len(analysis['issues'])
        state['messages'].append(
            AIMessage(content=f"🔬 Analysis complete. Found {issues_count} potential issues")
        )

        return state

    def generate_response(self, state: AgentState) -> AgentState:
        """Step 5: Generate comprehensive response"""
        user_query = state['user_query']
        analysis = state['analysis_results']

        # Prepare context for LLM
        context = self._prepare_context(analysis)

        system_prompt = """You are an expert code reviewer and assistant. Based on the analysis results,
provide a clear, helpful response to the user's query. Include:
1. Direct answer to their question
2. Relevant code snippets with file locations
3. Identified issues and suggestions
4. Best practices recommendations

Format your response with proper markdown, code blocks, and clear sections."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {user_query}\n\nAnalysis Results:\n{context}")
        ]

        response = self.llm.invoke(messages)

        state['current_step'] = "Response generated"
        state['messages'].append(AIMessage(content=response.content))

        return state

    def _prepare_context(self, analysis: Dict[str, Any]) -> str:
        """Prepare analysis results as context for LLM"""
        context_parts = []

        # Add search results
        if 'search_results' in analysis:
            results = analysis['search_results']
            context_parts.append(f"Files found: {len(results.get('files', []))}")
            context_parts.append(f"Code matches: {len(results.get('matches', []))}")

            # Add file names
            if results.get('files'):
                file_list = [f['path'] for f in results['files'][:10]]
                context_parts.append(f"Relevant files: {', '.join(file_list)}")

        # Add code analysis
        if 'code_analysis' in analysis:
            code_analysis = analysis['code_analysis']

            # Add issues
            if code_analysis.get('issues'):
                issues_summary = {}
                for issue in code_analysis['issues']:
                    severity = issue.get('severity', 'unknown')
                    issues_summary[severity] = issues_summary.get(severity, 0) + 1

                context_parts.append(f"Issues by severity: {issues_summary}")

            # Add suggestions
            if code_analysis.get('suggestions'):
                context_parts.append("Suggestions:")
                context_parts.extend(code_analysis['suggestions'][:5])

        return '\n'.join(context_parts)

    def run(self, user_query: str) -> List[Dict[str, Any]]:
        """Run the agent with a user query"""
        initial_state = {
            'messages': [],
            'repo_path': self.repo_path or '',
            'github_url': self.github_url or '',
            'current_step': 'start',
            'analysis_results': {},
            'user_query': user_query
        }

        final_state = self.graph.invoke(initial_state)

        # Format messages for return
        messages = []
        for msg in final_state['messages']:
            messages.append({
                'role': 'assistant' if isinstance(msg, AIMessage) else 'user',
                'content': msg.content
            })

        return messages
