#!/usr/bin/env bash

set -e  # exit on error

VENV_DIR=".venv"

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment..."
    python3.12 -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    # pip install pwrforge
else
    echo "[INFO] Activating virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
fi

echo "[INFO] Virtual environment is ready!"
echo "[INFO] Python: $(python --version)"
