#!/usr/bin/env bash
# bootstrap.sh — one-shot setup for a fresh clone of Flotilla.
#
# What it does:
#   1. Installs Hopewell git hooks (full set)
#   2. Refreshes Pedia + Mercator indexes
#   3. Prints a short status summary
#
# Requirements already satisfied by the README's pip installs:
#   pip install mercator hopewell pedia
#   pip install -e .

set -e

echo "=== Flotilla bootstrap ==="

# Tools may be installed without entry points on PATH; fall back to python -m.
hw()  { command -v hopewell >/dev/null 2>&1 && hopewell  "$@" || python -m hopewell  "$@"; }
pd()  { command -v pedia    >/dev/null 2>&1 && pedia     "$@" || python -m pedia     "$@"; }
mc()  { command -v mercator >/dev/null 2>&1 && mercator  "$@" || python -m mercator  "$@"; }

echo "[1/3] Installing Hopewell git hooks..."
hw hooks install --full --quiet || echo "      (hooks install returned non-zero — already installed?)"

echo "[2/3] Refreshing Pedia index..."
pd refresh || echo "      (pedia refresh failed — check .pedia/)"

echo "[3/3] Refreshing Mercator index..."
mc refresh 2>/dev/null || echo "      (mercator refresh skipped — may not have network yet)"

echo ""
echo "=== Status ==="
hw list 2>/dev/null | tail -10 || true
echo ""
pd query "notes" --format text 2>/dev/null | head -20 || true
echo ""
echo "Setup complete. Run: hopewell web --open"
