"""``flotilla search`` — Phase 2 stub.

Phase 1 ships with a curated registry of five plugins (taskflow, pedia,
codeatlas, diffsextant, slim-agents). A real search index over
third-party plugins arrives in Phase 2 — see
``patterns/drafts/flotilla-plugin-design.md`` section 7.
"""

from __future__ import annotations

import argparse


def cmd_search(args: argparse.Namespace) -> int:
    print(
        "flotilla search: deferred to Phase 2 — the marketplace index "
        "isn't published yet. In Phase 1, the curated plugins are:\n"
        "  taskflow    — work ledger\n"
        "  pedia       — knowledge base\n"
        "  codeatlas   — codemap\n"
        "  diffsextant — semantic-diff classifier\n"
        "  slim-agents — bare-bones 6-role AIDLC agent bundle\n"
        "Legacy names (hopewell, mercator, sextant) still resolve via "
        "registry aliases. Install any with `flotilla install <name>`."
    )
    return 0
