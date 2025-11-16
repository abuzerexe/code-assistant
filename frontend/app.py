"""
Streamlit Frontend for Code Assistant
Interactive chat interface with code analysis visualization
"""

import streamlit as st
import requests
import json
from pathlib import Path
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Code Assistant AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'repo_uploaded' not in st.session_state:
    st.session_state.repo_uploaded = False


def upload_zip_file(file):
    """Upload ZIP file to backend"""
    files = {'file': (file.name, file, 'application/zip')}
    try:
        response = requests.post(f"{API_URL}/upload/zip", files=files)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None


def clone_github_repo(repo_url):
    """Clone GitHub repository"""
    try:
        response = requests.post(
            f"{API_URL}/upload/github",
            json={"repo_url": repo_url}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Clone failed: {str(e)}")
        return None


def send_query(session_id, query):
    """Send query to agent"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"session_id": session_id, "query": query}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return None


# Header
st.markdown('<h1 class="main-header">🤖 Code Assistant AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">AI-powered code analysis, bug detection, and intelligent code review</p>',
    unsafe_allow_html=True
)

# Sidebar for repository upload
with st.sidebar:
    st.header("📁 Repository Setup")

    upload_method = st.radio(
        "Choose upload method:",
        ["GitHub URL", "ZIP Upload"],
        help="Select how you want to provide your codebase"
    )

    if upload_method == "GitHub URL":
        github_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repo",
            help="Enter the full GitHub repository URL"
        )

        if st.button("Clone Repository", type="primary"):
            if github_url:
                with st.spinner("Cloning repository..."):
                    result = clone_github_repo(github_url)
                    if result:
                        st.session_state.session_id = result['session_id']
                        st.session_state.repo_uploaded = True
                        st.success(f"✅ Cloned! Found {result['files_count']} files")
                        st.balloons()
            else:
                st.warning("Please enter a GitHub URL")

    else:  # ZIP Upload
        uploaded_file = st.file_uploader(
            "Upload ZIP file",
            type=['zip'],
            help="Upload a ZIP file containing your code repository"
        )

        if uploaded_file and st.button("Upload Repository", type="primary"):
            with st.spinner("Uploading and extracting..."):
                result = upload_zip_file(uploaded_file)
                if result:
                    st.session_state.session_id = result['session_id']
                    st.session_state.repo_uploaded = True
                    st.success(f"✅ Uploaded! Found {result['files_count']} files")
                    st.balloons()

    st.divider()

    # Session info
    if st.session_state.repo_uploaded:
        st.success("✅ Repository loaded")
        st.info(f"Session: {st.session_state.session_id[:8]}...")

        if st.button("Clear Session"):
            try:
                requests.delete(f"{API_URL}/session/{st.session_state.session_id}")
            except:
                pass
            st.session_state.session_id = None
            st.session_state.repo_uploaded = False
            st.session_state.messages = []
            st.rerun()
    else:
        st.warning("⚠️ No repository loaded")

    st.divider()

    # Example queries
    st.subheader("💡 Example Queries")
    examples = [
        "How does authentication work?",
        "Find potential security issues",
        "Explain the database structure",
        "Review the API endpoints",
        "Find all TODO comments",
        "Show me the main entry point"
    ]

    for example in examples:
        if st.button(example, key=f"ex_{example}", use_container_width=True):
            if st.session_state.repo_uploaded:
                st.session_state.example_query = example

# Main chat interface
if not st.session_state.repo_uploaded:
    # Welcome screen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### Welcome to Code Assistant AI!

        Get started by:
        1. 📁 Upload your code repository (ZIP or GitHub URL)
        2. 💬 Ask questions about your code
        3. 🔍 Get intelligent analysis and suggestions

        **Example queries:**
        - "How does authentication work in this project?"
        - "Find potential security vulnerabilities"
        - "Explain the database schema"
        - "Review the API implementation"
        """)

else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    query = st.chat_input("Ask me about your code...")

    # Handle example query
    if 'example_query' in st.session_state:
        query = st.session_state.example_query
        del st.session_state.example_query

    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your code..."):
                response = send_query(st.session_state.session_id, query)

                if response:
                    # Display all intermediate messages
                    for msg in response['messages']:
                        st.markdown(msg['content'])

                        # Add to session state
                        if msg not in st.session_state.messages:
                            st.session_state.messages.append(msg)

# Footer
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        Built with LangGraph, MCP, FastAPI & Streamlit<br>
        Week 9-10 Assignment | AI Agents Development
    </div>
    """, unsafe_allow_html=True)
