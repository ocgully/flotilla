#!/usr/bin/env bash
# bootstrap.sh — one-shot setup for a fresh clone of agentfactory-showcase.
#
# What it does:
#   1. Installs Hopewell git hooks (full set)
#   2. Refreshes Pedia + Mercator indexes
#   3. Annotates flow-network routes the hooks automate (auto_enforced)
#   4. Builds the Claude Code agent bundle from AgentFactory (if present)
#   5. Prints a short status summary
#
# Requirements already satisfied by the README's 3 pip installs:
#   pip install mercator hopewell pedia
#   pip install -e .

set -e

echo "=== agentfactory-showcase bootstrap ==="

# Tools may be installed without entry points on PATH; fall back to python -m.
hw()  { command -v hopewell >/dev/null 2>&1 && hopewell  "$@" || python -m hopewell  "$@"; }
pd()  { command -v pedia    >/dev/null 2>&1 && pedia     "$@" || python -m pedia     "$@"; }
mc()  { command -v mercator >/dev/null 2>&1 && mercator  "$@" || python -m mercator  "$@"; }

# 1. Install git hooks (full set: pre-commit + commit-msg + post-commit + pre-push)
echo "[1/5] Installing Hopewell git hooks..."
hw hooks install --full --quiet || echo "      (hooks install returned non-zero — already installed?)"

# 2. Refresh indexes
echo "[2/5] Refreshing Pedia index..."
pd refresh || echo "      (pedia refresh failed — check .pedia/)"

echo "[3/5] Refreshing Mercator index..."
mc refresh || echo "      (mercator refresh failed — may not have network yet)"

# 3. Annotate routes the hooks automate
echo "[4/5] Annotating auto-enforced flow routes..."
hw network annotate-auto-enforced --apply 2>/dev/null || echo "      (network not present — skipping)"

# 4. Build the core agent bundle if AgentFactory is on this machine
echo "[5/5] Building .claude/agents/ bundle..."
if [ -d "../AgentFactory/scripts" ]; then
  bash ../AgentFactory/scripts/build-bundle.sh
elif [ -d "../../AgentFactory/scripts" ]; then
  bash ../../AgentFactory/scripts/build-bundle.sh
else
  echo "      AgentFactory not found at ../AgentFactory or ../../AgentFactory"
  echo "      Clone it alongside this repo and re-run to populate .claude/agents/."
fi

# 5. Status summary
echo ""
echo "=== Status ==="
hw list 2>/dev/null | tail -10 || true
echo ""
pd query "notes" --format text 2>/dev/null | head -10 || true
echo ""
echo "Setup complete. Run 'hopewell web --open' to explore the canvas."
