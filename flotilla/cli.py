"""Flotilla command-line entry point.

Sub-commands implemented in Phase 1:

* ``init``     — scaffold ``.flotilla/`` in the current project
* ``install``  — install a plugin (resolve, compose, run on_install)
* ``list``     — show installed plugins + versions
* ``upgrade``  — re-resolve + recompose installed plugins
* ``remove``   — uninstall a plugin (un-compose, run on_uninstall, optionally pip uninstall)
* ``sync``     — re-read manifest, install/remove/upgrade to match
* ``validate`` — check a plugin repo for a valid flotilla.yaml + plugin/ layout
* ``doctor``   — diagnose missing deps, broken symlinks, version mismatches

Stubbed (Phase 2):

* ``search``   — query the marketplace index (deferred)
* ``info``     — show plugin README + reviews (deferred)

Each sub-command lives in ``flotilla.commands.<name>`` so the CLI stays
small and tests can drive sub-commands directly without re-parsing argv.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .__version__ import __version__
from .commands import (
    cmd_doctor,
    cmd_info,
    cmd_init,
    cmd_install,
    cmd_list,
    cmd_remove,
    cmd_search,
    cmd_sync,
    cmd_upgrade,
    cmd_validate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flotilla",
        description="Plugin marketplace for AI-native projects.",
    )
    parser.add_argument(
        "--version", action="version", version=f"flotilla {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p = sub.add_parser("init", help="scaffold .flotilla/ in the current dir")
    p.add_argument(
        "--path", default=".", help="project root (default: current directory)"
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing .flotilla/manifest.yaml + config.yaml",
    )

    # install
    p = sub.add_parser("install", help="install one or more plugins")
    p.add_argument("names", nargs="+", help="plugin names (curated) or paths")
    p.add_argument(
        "--source",
        default=None,
        help="for a single plugin: explicit repo URL or local path",
    )
    p.add_argument(
        "--version", default="*", help="version spec (default: latest)"
    )
    p.add_argument(
        "--extras", default="", help="comma-separated extras (pip plugins only)"
    )
    p.add_argument(
        "--no-run-install",
        action="store_true",
        help="skip on_install steps (compose only)",
    )

    # list
    p = sub.add_parser("list", help="show installed plugins")
    p.add_argument(
        "--format", choices=("text", "json"), default="text", help="output format"
    )

    # upgrade
    p = sub.add_parser("upgrade", help="re-resolve + recompose installed plugins")
    p.add_argument("name", nargs="?", help="single plugin (default: all)")

    # remove
    p = sub.add_parser("remove", help="uninstall a plugin")
    p.add_argument("name", help="plugin name")
    p.add_argument(
        "--keep-pip",
        action="store_true",
        help="for tool plugins: leave the pip package installed",
    )
    p.add_argument(
        "--no-run-uninstall",
        action="store_true",
        help="skip on_uninstall steps",
    )

    # sync
    p = sub.add_parser(
        "sync",
        help="re-resolve everything in .flotilla/manifest.yaml (install missing, remove orphaned)",
    )

    # validate
    p = sub.add_parser(
        "validate", help="check a plugin repo for a valid flotilla.yaml"
    )
    p.add_argument("path", nargs="?", default=".", help="path to plugin repo")

    # doctor
    p = sub.add_parser("doctor", help="diagnose project health")

    # search (Phase 2)
    p = sub.add_parser("search", help="(deferred to Phase 2) query the index")
    p.add_argument("query", nargs="?", default="")

    # info (Phase 2)
    p = sub.add_parser("info", help="(deferred to Phase 2) show plugin info")
    p.add_argument("name", nargs="?", default="")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    handlers = {
        "init": cmd_init,
        "install": cmd_install,
        "list": cmd_list,
        "upgrade": cmd_upgrade,
        "remove": cmd_remove,
        "sync": cmd_sync,
        "validate": cmd_validate,
        "doctor": cmd_doctor,
        "search": cmd_search,
        "info": cmd_info,
    }
    handler = handlers[args.command]
    try:
        return int(handler(args) or 0)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover — user-facing error path
        print(f"flotilla: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
