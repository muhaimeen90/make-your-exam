#!/bin/bash

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "Stopping ExamForge..."
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    if [ -n "$FRONTEND_PID" ]; then kill $FRONTEND_PID; fi
    exit
}

# Trap Ctrl+C (SIGINT)
trap cleanup SIGINT

echo "Starting ExamForge in this terminal..."

# Start Backend
echo "[1/2] Starting Backend..."
cd backend
source venv/bin/activate
# Run in background, redirect output to keep it slightly cleaner or just let it flow
uvicorn main:app --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# Start Frontend
echo "[2/2] Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "------------------------------------------------"
echo "ExamForge is running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both servers."
echo "------------------------------------------------"

# Wait for processes to finish
wait
