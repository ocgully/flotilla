#!/usr/bin/env bash
# bootstrap.sh — one-shot setup for a fresh clone of Flotilla.
#
# What it does:
#   1. Installs TaskFlow git hooks (full set)
#   2. Refreshes Pedia + CodeAtlas indexes
#   3. Prints a short status summary
#
# Requirements already satisfied by the README's pip installs:
#   pip install codeatlas taskflow pedia
#   pip install -e .

set -e

echo "=== Flotilla bootstrap ==="

# Tools may be installed without entry points on PATH; fall back to python -m.
# (taskflow ships a `hopewell` deprecation alias, so older invocations still work.)
tf()  { command -v taskflow  >/dev/null 2>&1 && taskflow  "$@" || python -m taskflow  "$@"; }
pd()  { command -v pedia     >/dev/null 2>&1 && pedia     "$@" || python -m pedia     "$@"; }
ca()  { command -v codeatlas >/dev/null 2>&1 && codeatlas "$@" || python -m codeatlas "$@"; }

echo "[1/3] Installing TaskFlow git hooks..."
tf hooks install --full --quiet || echo "      (hooks install returned non-zero — already installed?)"

echo "[2/3] Refreshing Pedia index..."
pd refresh || echo "      (pedia refresh failed — check .pedia/)"

echo "[3/3] Refreshing CodeAtlas index..."
ca refresh 2>/dev/null || echo "      (codeatlas refresh skipped — may not have network yet)"

echo ""
echo "=== Status ==="
tf list 2>/dev/null | tail -10 || true
echo ""
pd query "notes" --format text 2>/dev/null | head -20 || true
echo ""
echo "Setup complete. Run: taskflow web --open"
