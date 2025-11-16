#!/bin/bash
# Script to run Code Assistant locally

echo "🚀 Starting Code Assistant..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API keys"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start backend in background
echo "🔌 Starting FastAPI backend..."
cd backend
python api.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting Streamlit frontend..."
cd frontend
streamlit run app.py

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
