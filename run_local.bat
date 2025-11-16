@echo off
REM Script to run Code Assistant locally on Windows

echo Starting Code Assistant...

REM Check if .env exists
if not exist .env (
    echo .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env and add your API keys
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Start backend in background
echo Starting FastAPI backend...
start /B python backend\api.py

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting Streamlit frontend...
cd frontend
streamlit run app.py
