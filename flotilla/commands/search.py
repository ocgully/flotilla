"""``flotilla search`` — Phase 2 stub.

Phase 1 ships with a curated registry of four plugins (hopewell, pedia,
mercator, slim-agents). A real search index over third-party plugins
arrives in Phase 2 — see ``patterns/drafts/flotilla-plugin-design.md``
section 7.
"""

from __future__ import annotations

import argparse


def cmd_search(args: argparse.Namespace) -> int:
    print(
        "flotilla search: deferred to Phase 2 — the marketplace index "
        "isn't published yet. In Phase 1, the curated plugins are:\n"
        "  hopewell    — work ledger\n"
        "  pedia       — knowledge base\n"
        "  mercator    — codemap\n"
        "  slim-agents — bare-bones 6-role AIDLC agent bundle\n"
        "Install any of them with `flotilla install <name>`."
    )
    return 0
