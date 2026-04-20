#!/bin/bash
export PATH="/home/rafan/HF26-24/tools/$(ls $TOOLS_DIR | grep node-v | head -n 1)/bin:$PATH"
cd "/home/rafan/HF26-24/frontend"
echo "🌐 Launching Frontend on Port 3000..."
npm run dev 2>&1
