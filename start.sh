#!/bin/bash

# Start ArcFlux Backend and Frontend

echo "🚀 Starting ArcFlux..."
echo ""

# Check if backend is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Backend is already running on port 8000"
else
    echo "�� Starting Backend..."
    cd backend-python
    conda run -n arcpay python main.py &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
    cd ..
    sleep 3
fi

# Check if frontend is already running
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "⚠️  Frontend is already running on port 5173"
else
    echo "📦 Starting Frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
    cd ..
fi

echo ""
echo "✅ ArcFlux is starting!"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "�� Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for user interrupt
wait
