#!/bin/bash

echo "🧬 Starting Oxia: The Metabolic Digital Twin..."

# Ensure we are in the virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

source .venv/bin/activate

# Trap CMD+C to close both servers gracefully
trap 'echo "🛑 Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT TERM

# Start the FastAPI backend in the background
echo "🔌 Starting FastAPI Backend on port 8000..."
uvicorn backend:app --port 8000 &
BACKEND_PID=$!

# Wait a second to let the backend initialize
sleep 2

# Start the Streamlit frontend
echo "🎨 Starting Streamlit Frontend on port 8501..."
streamlit run app.py --server.port 8501 &
FRONTEND_PID=$!

echo "✅ Both servers are running! Press CMD+C to stop them."

# Wait indefinitely so the script doesn't exit, allowing the trap to catch CMD+C
wait
