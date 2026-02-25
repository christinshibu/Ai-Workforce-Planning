#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[1/5] Creating virtual environment at .venv"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  echo "[1/5] Reusing existing virtual environment at .venv"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[2/5] Installing dependencies"
pip install -r "${PROJECT_ROOT}/requirements.txt"

echo "[3/5] Applying database migrations"
python "${PROJECT_ROOT}/manage.py" migrate

echo "[4/5] Seeding demo users and staff"
python "${PROJECT_ROOT}/manage.py" seed_demo

echo "[5/5] Starting server at http://localhost:8000"
exec daphne -b 0.0.0.0 -p 8000 his_workforce.asgi:application
