"""Command-line interface for the notes showcase.

Keep it stdlib-only; keep it under the 300-LOC budget (constitution).
"""

from __future__ import annotations

import argparse
import sys

from . import __version__, store


def _cmd_add(args: argparse.Namespace) -> int:
    note = store.add(args.text)
    print(note.render())
    return 0


def _cmd_list(_: argparse.Namespace) -> int:
    notes = store.load()
    if not notes:
        print("(no notes — add one with `notes add \"...\"`)")
        return 0
    for n in notes:
        print(n.render())
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    matches = store.search(args.query)
    if not matches:
        print(f"(no matches for {args.query!r})")
        return 0
    for n in matches:
        print(n.render())
    return 0


def _cmd_done(args: argparse.Namespace) -> int:
    try:
        n = store.mark_done(args.id)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(n.render())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="notes",
        description="Plain-text notes CLI (the showcase domain).",
    )
    p.add_argument("--version", action="version", version=f"notes {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="Append a new note.")
    a.add_argument("text", help="Note text.")
    a.set_defaults(func=_cmd_add)

    l = sub.add_parser("list", help="List all notes.")
    l.set_defaults(func=_cmd_list)

    s = sub.add_parser("search", help="Find notes containing a substring.")
    s.add_argument("query", help="Case-insensitive substring.")
    s.set_defaults(func=_cmd_search)

    d = sub.add_parser("done", help="Mark a note as done by id.")
    d.add_argument("id", type=int, help="1-based note id (see `notes list`).")
    d.set_defaults(func=_cmd_done)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
