#!/bin/bash

# ====================================================================
# ProtEngine Labs — Smart Discovery Pipeline Setup & Launcher
# ====================================================================
# This script handles interactive environment setup and service launch.
# ====================================================================

set -e 

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOOLS_DIR="$PROJECT_ROOT/tools"
CONFIG_FILE="$PROJECT_ROOT/.setup_config"
mkdir -p "$TOOLS_DIR"

echo "🧬 ProtEngine Labs — System Intelligence"
echo "=========================================="

# --- 1. Load/Check Configuration ---
SKIP_SETUP=false
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    if [ "$SETUP_COMPLETE" = "true" ]; then
        echo "✅ Setup already complete. Skipping to launch... (Delete .setup_config to reset)"
        SKIP_SETUP=true
    fi
fi

# --- 2. OS Detection ---
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)     OS="Linux";;
    Darwin*)    OS="MacOS";;
    *)          OS="Unknown"; echo "❌ Unsupported OS: $OS_TYPE"; exit 1;;
esac

# --- 3. Interactive Setup ---
if [ "$SKIP_SETUP" = false ]; then
    # Detect Conda/Mamba
    CONDA_EXE=$(which mamba || which conda || echo "")
    
    if [ -n "$CONDA_EXE" ]; then
        echo "🔍 Global environment manager detected: $CONDA_EXE"
        
        # Check if current env has required tools
        TOOLS_MISSING=false
        command -v vina >/dev/null 2>&1 || TOOLS_MISSING=true
        command -v fpocket >/dev/null 2>&1 || TOOLS_MISSING=true
        command -v obabel >/dev/null 2>&1 || TOOLS_MISSING=true
        
        if [ "$TOOLS_MISSING" = false ]; then
            echo "🟢 Bio-informatics tools detected in current path. Systems ready."
            read -p "❓ Re-verify and install Python dependencies? [y/N]: " REVERIFY
            [[ ! "$REVERIFY" =~ ^[Yy]$ ]] && SKIP_SETUP=true
        else
            echo "⚠️  Bio-informatics tools (Vina/fpocket/OpenBabel) are missing."
            echo "Options:"
            echo "  1) Install in CURRENT environment (Active: ${CONDA_DEFAULT_ENV:-base})"
            echo "  2) Create NEW environment 'protengine'"
            echo "  3) Skip installation (I will handle it manually)"
            read -p "Select [1/2/3]: " CHOICE
            
            case "$CHOICE" in
                1) echo "📦 Installing in current environment..."; ENV_NAME="${CONDA_DEFAULT_ENV:-base}";;
                2) echo "📦 Creating new environment..."; ENV_NAME="protengine"; conda create -y -n "$ENV_NAME" python=3.11;;
                *) echo "⏭️  Skipping installation."; SKIP_SETUP=true;;
            esac
        fi
    fi
fi

# --- 4. Core Installation (If not skipped) ---
if [ "$SKIP_SETUP" = false ]; then
    echo "🧪 Synchronizing Bio-informatics dependencies..."
    conda install -y -c conda-forge vina fpocket openbabel rdkit numpy pip -n "${ENV_NAME:-protengine}" || true
    
    source "$(dirname "$CONDA_EXE")/../etc/profile.d/conda.sh" || true
    conda activate "${ENV_NAME:-protengine}" || true
    
    echo "📦 Synchronizing backend python packages..."
    cd "$PROJECT_ROOT/backend"
    pip install -r requirements.txt -q
    pip install "urllib3<2.0" -q
    
    # Node.js Check
    cd "$PROJECT_ROOT"
    if ! command -v node >/dev/null 2>&1; then
        echo "🟢 Node.js missing. Installing local Node.js v20..."
        NODE_VERSION="20.11.0"
        NODE_DIST="node-v$NODE_VERSION-linux-x86_64"
        [ "$OS" == "MacOS" ] && NODE_DIST="node-v$NODE_VERSION-darwin-arm64"
        if [ ! -d "$TOOLS_DIR/$NODE_DIST" ]; then
            curl -L "https://nodejs.org/dist/v$NODE_VERSION/$NODE_DIST.tar.xz" -o "$TOOLS_DIR/node.tar.xz"
            tar -xJf "$TOOLS_DIR/node.tar.xz" -C "$TOOLS_DIR"
            rm "$TOOLS_DIR/node.tar.xz"
        fi
        export PATH="$TOOLS_DIR/$NODE_DIST/bin:$PATH"
    fi

    echo "🎨 Setting up frontend..."
    cd "$PROJECT_ROOT/frontend"
    npm install --no-audit --no-fund --silent
    
    # Save config
    echo "SETUP_COMPLETE=true" > "$CONFIG_FILE"
    echo "ENV_NAME=${ENV_NAME:-protengine}" >> "$CONFIG_FILE"
    echo "✅ Setup finalized and saved."
fi

# --- 5. Service Launch ---
cd "$PROJECT_ROOT"
echo "======================================"
echo "🚀 ProtEngine Labs READY"
echo "======================================"

# Persistence check for env activation
[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"
ENV_TO_ACTIVATE="${ENV_NAME:-protengine}"

# Ensure run scripts use full paths and logging
cat > "$TOOLS_DIR/run_backend.sh" << EOF
#!/bin/bash
source "\$(which conda | sed 's|/bin/conda||')/etc/profile.d/conda.sh" || true
conda activate "$ENV_TO_ACTIVATE" || echo "⚠️  Env activation failed, trying anyway..."
cd "$PROJECT_ROOT/backend"
echo "📡 Launching Backend on Port 7860..."
uvicorn main:app --reload --host 0.0.0.0 --port 7860 2>&1
EOF
chmod +x "$TOOLS_DIR/run_backend.sh"

cat > "$TOOLS_DIR/run_frontend.sh" << EOF
#!/bin/bash
NODE_BIN_DIR=\$(ls \$TOOLS_DIR | grep node-v | head -n 1)
if [ -n "\$NODE_BIN_DIR" ]; then
  export PATH="\$TOOLS_DIR/\$NODE_BIN_DIR/bin:\$PATH"
fi
cd "$PROJECT_ROOT/frontend"
echo "🌐 Launching Frontend on Port 3000..."
npm run dev 2>&1
EOF
chmod +x "$TOOLS_DIR/run_frontend.sh"

# Determine terminal and launch with 'Hold' flags
LAUNCH_CMD=""
if command -v xfce4-terminal >/dev/null 2>&1; then
    # -H keeps the terminal open after the command exits
    xfce4-terminal -H --title="ProtEngine Backend" -e "$TOOLS_DIR/run_backend.sh" &
    sleep 2
    xfce4-terminal -H --title="ProtEngine Frontend" -e "$TOOLS_DIR/run_frontend.sh" &
elif command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --title="ProtEngine Backend" -- bash -c "$TOOLS_DIR/run_backend.sh; exec bash" &
    sleep 2
    gnome-terminal --title="ProtEngine Frontend" -- bash -c "$TOOLS_DIR/run_frontend.sh; exec bash" &
else
    echo "⚠️  No terminal emulator found. Running in background..."
    bash "$TOOLS_DIR/run_backend.sh" &
    bash "$TOOLS_DIR/run_frontend.sh" &
fi

echo ""
echo "📡 Backend Status: http://localhost:7860"
echo "🌐 Frontend Status: http://localhost:3000"
echo "--------------------------------------"
echo "Control-C here to exit this manager."
wait
