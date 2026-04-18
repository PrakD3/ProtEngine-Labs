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
