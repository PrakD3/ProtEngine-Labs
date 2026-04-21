#!/bin/bash
NODE_BIN_DIR=$(ls $TOOLS_DIR | grep node-v | head -n 1)
if [ -n "$NODE_BIN_DIR" ]; then
  export PATH="$TOOLS_DIR/$NODE_BIN_DIR/bin:$PATH"
fi
cd "/home/rafan/HF26-24/frontend"
echo "🌐 Launching Frontend on Port 3000..."
npm run dev 2>&1
