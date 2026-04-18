#!/bin/bash
cd "$(dirname "$0")/backend"

# Setup environment
if [ ! -f ".env" ]; then
    [ -f ".env.example" ] && cp .env.example .env
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing backend dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

echo ""
echo "🚀 Backend Starting..."
echo "📡 API: http://localhost:8000"
echo "📖 Docs: http://localhost:8000/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Keep terminal open on exit
read -p "Press Enter to close..."
