#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POSES_DIR="$ROOT_DIR/backend/data/docked_poses"

if [[ ! -d "$POSES_DIR" ]]; then
  echo "docked_poses directory not found: $POSES_DIR"
  exit 0
fi

find "$POSES_DIR" -mindepth 1 -exec rm -rf {} +

echo "Cleared docked poses in $POSES_DIR"
