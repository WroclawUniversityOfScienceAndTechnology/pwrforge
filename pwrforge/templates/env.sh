#!/usr/bin/env bash

set -e  # exit on error

VENV_DIR=".venv"

# -------------------------
# 1) Create venv if missing
# -------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment..."
    python3.12 -m venv "$VENV_DIR"

    echo "[INFO] Activating virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    echo "[INFO] Upgrading pip..."
    pip install --upgrade pip

    echo "[INFO] Installing project dependencies..."
    pip install -e ".[dev]"  # jeśli masz extras 'dev'; inaczej usuń
else
    echo "[INFO] Virtual environment exists."
    echo "[INFO] Activating..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
fi

echo "[INFO] Virtual environment is ready!"
echo "[INFO] Python: $(python --version)"
