"""``flotilla info`` — Phase 2 stub.

In Phase 1, basic plugin info comes from the curated registry. The
richer "show plugin README + reviews" experience is Phase 2.
"""

from __future__ import annotations

import argparse

from ..registry import lookup


def cmd_info(args: argparse.Namespace) -> int:
    if not args.name:
        print(
            "flotilla info: deferred to Phase 2 (no marketplace index yet). "
            "Pass a plugin name to see the registry stub."
        )
        return 0
    known = lookup(args.name)
    if known is None:
        print(f"flotilla info {args.name}: not in the curated registry")
        return 1
    print(f"{known.name} ({known.kind})")
    print(f"  description: {known.description}")
    if known.pip_package:
        print(f"  pip:         {known.pip_package}")
    if known.repo:
        print(f"  repo:        {known.repo}")
    print(
        "  (full README + reviews deferred to Phase 2 — for now, see the "
        "repo URL above.)"
    )
    return 0
