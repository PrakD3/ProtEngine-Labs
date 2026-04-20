#!/bin/bash
source "$(which conda | sed 's|/bin/conda||')/etc/profile.d/conda.sh" || true
conda activate "protengine" || echo "⚠️  Env activation failed, trying anyway..."
cd "/home/rafan/HF26-24/backend"
echo "📡 Launching Backend on Port 7860..."
uvicorn main:app --reload --host 0.0.0.0 --port 7860 2>&1
