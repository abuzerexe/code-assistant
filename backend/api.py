"""
FastAPI Backend for Code Assistant
Provides REST API endpoints for the agent
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import git
from dotenv import load_dotenv

from agent import CodeAssistantAgent

load_dotenv()

app = FastAPI(
    title="Code Assistant API",
    description="AI-powered code analysis and assistance",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions
sessions: Dict[str, CodeAssistantAgent] = {}
temp_dirs: Dict[str, str] = {}


class QueryRequest(BaseModel):
    session_id: str
    query: str


class UploadResponse(BaseModel):
    session_id: str
    message: str
    files_count: int


class QueryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]


class GitHubRequest(BaseModel):
    repo_url: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Code Assistant API",
        "version": "1.0.0"
    }


@app.post("/upload/zip", response_model=UploadResponse)
async def upload_zip(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload a ZIP file containing code repository"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="code_assistant_")
    session_id = Path(temp_dir).name

    try:
        # Save uploaded file
        zip_path = Path(temp_dir) / file.filename
        with open(zip_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # Extract ZIP
        extract_dir = Path(temp_dir) / "repo"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Count files
        files_count = len(list(extract_dir.rglob('*.*')))

        # Create agent session
        agent = CodeAssistantAgent(repo_path=str(extract_dir))
        sessions[session_id] = agent
        temp_dirs[session_id] = temp_dir

        return UploadResponse(
            session_id=session_id,
            message="Repository uploaded successfully",
            files_count=files_count
        )

    except Exception as e:
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to process ZIP: {str(e)}")


@app.post("/upload/github", response_model=UploadResponse)
async def upload_github(request: GitHubRequest):
    """Clone a GitHub repository"""
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="code_assistant_")
        session_id = Path(temp_dir).name

        # Clone repository
        repo_dir = Path(temp_dir) / "repo"
        git.Repo.clone_from(request.repo_url, repo_dir, depth=1)

        # Count files
        files_count = len(list(repo_dir.rglob('*.*')))

        # Create agent session with both local path and GitHub URL
        agent = CodeAssistantAgent(
            repo_path=str(repo_dir),
            github_url=request.repo_url
        )
        sessions[session_id] = agent
        temp_dirs[session_id] = temp_dir

        return UploadResponse(
            session_id=session_id,
            message="GitHub repository cloned successfully",
            files_count=files_count
        )

    except git.GitCommandError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Send a query to the code assistant agent"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a repository first.")

    try:
        agent = sessions[request.session_id]
        messages = agent.run(request.query)

        return QueryResponse(
            session_id=request.session_id,
            messages=messages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and cleanup temporary files"""
    if session_id in sessions:
        del sessions[session_id]

    if session_id in temp_dirs:
        temp_dir = temp_dirs[session_id]
        shutil.rmtree(temp_dir, ignore_errors=True)
        del temp_dirs[session_id]

    return {"message": "Session deleted successfully"}


@app.get("/sessions")
async def list_sessions():
    """List active sessions"""
    return {
        "sessions": list(sessions.keys()),
        "count": len(sessions)
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    for temp_dir in temp_dirs.values():
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
