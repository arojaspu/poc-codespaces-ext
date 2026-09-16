#!/usr/bin/env bash
set -euo pipefail

echo "==> Dependencias de la app"
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

echo "==> ext_guard"
pip install -e ./tools

echo "==> Snapshot de linea base (CP-01)"
python -m ext_guard check --json --label baseline-post-create || true

echo "==> Listo. Ejecuta 'python -m ext_guard check' cuando quieras."
