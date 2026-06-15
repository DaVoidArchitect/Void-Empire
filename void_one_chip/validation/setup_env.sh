#!/usr/bin/env bash
set -euo pipefail

echo "[void-one] setting up local Void One validation environment"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[void-one][error] python3 not found" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip wheel setuptools
python -m pip install -r "$ROOT_DIR/validation/requirements.txt"

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y yosys boolector
fi

if ! command -v sby >/dev/null 2>&1; then
  echo "[void-one] installing SymbiYosys locally"
  python -m pip install symbiyosys
fi

if ! command -v yosys >/dev/null 2>&1; then
  echo "[void-one][warn] yosys not found in PATH. Install yosys manually for formal verification."
fi

echo "[void-one] environment setup complete"
