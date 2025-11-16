# 🤖 Code Assistant AI

An intelligent AI-powered code analysis assistant built with **LangGraph**, **Model Context Protocol (MCP)**, **FastAPI**, and **Streamlit**. Get instant insights, bug detection, code reviews, and intelligent explanations for any codebase.

![Code Assistant Demo](https://via.placeholder.com/800x400.png?text=Code+Assistant+AI+Demo)

## 🎯 Problem Statement

Developers spend countless hours:
- Understanding unfamiliar codebases
- Manually reviewing code for bugs and security issues
- Searching through large projects for specific functionality
- Documenting code architecture and dependencies

**Code Assistant AI** solves this by providing an intelligent agent that can:
- ✅ Analyze code structure and explain how things work
- ✅ Detect potential bugs, security vulnerabilities, and code smells
- ✅ Review code quality and suggest improvements
- ✅ Search across files with semantic understanding
- ✅ Generate documentation and architectural insights

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│                  (Streamlit Chat UI)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LangGraph Agent                          │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Step 1: Understand Query (Intent Detection)   │  │  │
│  │  └────────────────┬───────────────────────────────┘  │  │
│  │  ┌────────────────▼───────────────────────────────┐  │  │
│  │  │  Step 2: Plan Search (File/Pattern Selection)  │  │  │
│  │  └────────────────┬───────────────────────────────┘  │  │
│  │  ┌────────────────▼───────────────────────────────┐  │  │
│  │  │  Step 3: Execute Search (MCP Calls)            │  │  │
│  │  └────────────────┬───────────────────────────────┘  │  │
│  │  ┌────────────────▼───────────────────────────────┐  │  │
│  │  │  Step 4: Analyze Code (Static Analysis)        │  │  │
│  │  └────────────────┬───────────────────────────────┘  │  │
│  │  ┌────────────────▼───────────────────────────────┐  │  │
│  │  │  Step 5: Generate Response (LLM Synthesis)     │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼─────┐ ┌──────▼──────┐ ┌────▼──────────┐
│   File      │ │   GitHub    │ │     Code      │
│   System    │ │   API       │ │   Analyzer    │
│   MCP       │ │   MCP       │ │   MCP         │
└─────────────┘ └─────────────┘ └───────────────┘
```

## 🚀 Features

### Core Capabilities
- **🔍 Intelligent Code Search**: Semantic search across your entire codebase
- **🐛 Bug Detection**: Identify potential security issues, code smells, and anti-patterns
- **📊 Code Analysis**: Complexity metrics, maintainability index, and quality scores
- **💡 Smart Explanations**: Understand authentication, APIs, database schemas, etc.
- **📝 Code Review**: Get improvement suggestions and best practices recommendations
- **🔗 GitHub Integration**: Directly analyze public GitHub repositories

### Technical Features
- **Multi-step Reasoning**: LangGraph orchestrates a 5-step analysis workflow
- **MCP Integration**: Three custom MCP servers for file system, GitHub, and code analysis
- **Async Processing**: FastAPI backend handles multiple concurrent sessions
- **Real-time Feedback**: See the agent's thinking process step-by-step
- **Session Management**: Maintain context across multiple queries

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | LangGraph (LangChain) |
| **Context Protocol** | Model Context Protocol (MCP) |
| **LLM** | OpenAI GPT-4 / Anthropic Claude / OpenRouter (100+ models) |
| **Backend** | FastAPI (Python 3.11) |
| **Frontend** | Streamlit |
| **Code Analysis** | Radon, AST, Tree-sitter |
| **Deployment** | Render (Backend) + Streamlit Cloud (Frontend) |

## 📦 Installation

### Prerequisites
- Python 3.11+
- Git
- API Key: OpenAI **OR** Anthropic **OR** OpenRouter (recommended - access to 100+ models)

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/code-assistant.git
cd code-assistant
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
```env
# Option 1: OpenRouter (recommended - access to 100+ models)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4-turbo-preview

# Option 2: OpenAI
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Option 3: Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
```

**Using OpenRouter?** See [OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md) for model options and pricing.

5. **Run with Docker Compose (Recommended)**
```bash
docker-compose up
```

Or run separately:

**Backend:**
```bash
cd backend
python api.py
# Runs on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
streamlit run app.py
# Runs on http://localhost:8501
```

## 🎮 Usage

### 1. Upload Your Code

**Option A: GitHub URL**
- Enter any public GitHub repository URL
- Example: `https://github.com/pallets/flask`

**Option B: ZIP Upload**
- Package your code as a ZIP file
- Upload through the web interface

### 2. Ask Questions

Example queries:

**Code Explanation:**
```
"How does authentication work in this project?"
"Explain the database schema"
"What is the main entry point?"
```

**Bug Detection:**
```
"Find potential security vulnerabilities"
"Check for code smells in the authentication module"
"Are there any hardcoded credentials?"
```

**Code Review:**
```
"Review the API implementation"
"Suggest improvements for the payment processing code"
"Check for missing error handling"
```

**Architecture:**
```
"What is the overall structure of this project?"
"Show me the dependencies between modules"
"How are different components connected?"
```

### 3. Get Intelligent Responses

The agent will:
1. 🔍 Understand your question
2. 📋 Plan which files to search
3. 📁 Execute the search
4. 🔬 Analyze the code
5. ✅ Generate a comprehensive response with:
   - Code snippets with file locations
   - Identified issues
   - Improvement suggestions
   - Best practices recommendations

## 🌐 Deployment

### Deploy Backend to Render

1. Push your code to GitHub
2. Connect to Render: https://render.com
3. Create new Web Service
4. Use `render.yaml` configuration
5. Add environment variables (API keys)
6. Deploy!

### Deploy Frontend to Streamlit Cloud

1. Push to GitHub
2. Go to https://streamlit.io/cloud
3. Create new app
4. Point to `frontend/app.py`
5. Add secrets (API_URL pointing to Render backend)
6. Deploy!

### Environment Variables for Deployment

**Render (Backend):**
```
OPENAI_API_KEY=your-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```

**Streamlit Cloud (Frontend):**
```toml
# .streamlit/secrets.toml
API_URL = "https://your-render-backend.onrender.com"
```

## 📊 How MCP Improves Context Awareness

### Before MCP:
- Manual file reading
- No structured context
- Hard to integrate external tools
- Limited code understanding

### With MCP:
✅ **File System MCP**: Structured access to repository files with smart filtering
✅ **GitHub MCP**: Direct integration with GitHub API for remote repos
✅ **Code Analyzer MCP**: Dedicated static analysis tools (complexity, metrics, issues)
✅ **Standardized Interface**: All tools expose consistent interfaces to the agent
✅ **Context Enrichment**: Each MCP server provides rich metadata about code structure

**Example Flow:**
```python
User: "Find authentication bugs"
  ↓
LangGraph Agent Plans:
  - Use File System MCP to search for auth-related files
  - Use Code Analyzer MCP to check for security issues
  - Use GitHub MCP to check recent commits in auth module
  ↓
MCP Servers Return:
  - Structured file list with metadata
  - Security issues with severity levels
  - Commit history with context
  ↓
Agent Synthesizes:
  - "Found 3 critical issues in auth.py:45, auth.py:78..."
  - "Recent commit added unsafe password handling..."
```



## 🧪 Testing

Run backend tests:
```bash
cd backend
pytest tests/
```

Test API endpoints:
```bash
# Health check
curl http://localhost:8000/

# Upload GitHub repo
curl -X POST http://localhost:8000/upload/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/pallets/flask"}'
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🙏 Acknowledgments

- **LangChain Team** for LangGraph framework
- **Anthropic** for Model Context Protocol specification
- **FastAPI** for the excellent async framework
- **Streamlit** for the rapid UI development

## 📧 Contact

**Developer:** Abuzer
**Email:** abouzer381@gmail.com
**GitHub:** [@abuzerexe](https://github.com/abuzerexe)

**Built with ❤️ using LangGraph, MCP, FastAPI & Streamlit**

