#!/bin/bash

# AXONENGINE v4.0 — Drug Discovery AI Quick Start (Separate Terminals)
# ====================================================================

echo "🧬 Drug Discovery AI — Quick Start (Separate Terminals)"
echo "========================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect available terminal emulator
TERMINAL=""
if command -v gnome-terminal &> /dev/null; then
    TERMINAL="gnome-terminal"
elif command -v xterm &> /dev/null; then
    TERMINAL="xterm"
elif command -v konsole &> /dev/null; then
    TERMINAL="konsole"
elif command -v xfce4-terminal &> /dev/null; then
    TERMINAL="xfce4-terminal"
fi

# ── Backend Launcher Script ──────────────────────────────────────────────────
cat > "$SCRIPT_DIR/backend_launcher.sh" << 'BACKEND_SCRIPT'
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
BACKEND_SCRIPT

chmod +x "$SCRIPT_DIR/backend_launcher.sh"

# ── Frontend Launcher Script ─────────────────────────────────────────────────
cat > "$SCRIPT_DIR/frontend_launcher.sh" << 'FRONTEND_SCRIPT'
#!/bin/bash
cd "$(dirname "$0")/frontend"

if [ ! -f ".env.local" ]; then
    cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
fi

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo ""
echo "🚀 Frontend Starting..."
echo "🌐 App: http://localhost:3000"
echo ""

npm run dev

# Keep terminal open on exit
read -p "Press Enter to close..."
FRONTEND_SCRIPT

chmod +x "$SCRIPT_DIR/frontend_launcher.sh"

# ── Launch Terminals ────────────────────────────────────────────────────────
echo "Launching services in separate terminals..."
echo ""

if [ "$TERMINAL" = "gnome-terminal" ]; then
    gnome-terminal -- bash -c "$SCRIPT_DIR/backend_launcher.sh" &
    sleep 1
    gnome-terminal -- bash -c "$SCRIPT_DIR/frontend_launcher.sh" &
    
elif [ "$TERMINAL" = "xterm" ]; then
    xterm -e bash "$SCRIPT_DIR/backend_launcher.sh" &
    sleep 1
    xterm -e bash "$SCRIPT_DIR/frontend_launcher.sh" &
    
elif [ "$TERMINAL" = "konsole" ]; then
    konsole -e bash "$SCRIPT_DIR/backend_launcher.sh" &
    sleep 1
    konsole -e bash "$SCRIPT_DIR/frontend_launcher.sh" &
    
elif [ "$TERMINAL" = "xfce4-terminal" ]; then
    xfce4-terminal -e "bash $SCRIPT_DIR/backend_launcher.sh" &
    sleep 1
    xfce4-terminal -e "bash $SCRIPT_DIR/frontend_launcher.sh" &
    
else
    echo "❌ No compatible terminal emulator found."
    echo ""
    echo "Install one of: gnome-terminal, xterm, konsole, xfce4-terminal"
    echo ""
    echo "Or run manually:"
    echo "  Terminal 1: bash $SCRIPT_DIR/backend_launcher.sh"
    echo "  Terminal 2: bash $SCRIPT_DIR/frontend_launcher.sh"
    exit 1
fi

echo "✅ Services launching in separate terminals..."
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Close the terminal windows to stop services."
