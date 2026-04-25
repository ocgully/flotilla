"""``flotilla list`` — show installed plugins."""

from __future__ import annotations

import argparse
import json

from ..installed import load_db
from ..paths import ProjectPaths, require_project_root


def cmd_list(args: argparse.Namespace) -> int:
    project = ProjectPaths(root=require_project_root())
    db = load_db(project.installed_db)
    if args.format == "json":
        payload = [
            {
                "name": p.name,
                "version": p.version,
                "kind": p.kind,
                "source": p.source,
                "files": len(p.contributed_files),
                "settings_keys": list(p.settings_keys),
            }
            for p in sorted(db.plugins.values(), key=lambda x: x.name)
        ]
        print(json.dumps(payload, indent=2))
        return 0
    if not db.plugins:
        print("flotilla: no plugins installed (run `flotilla install <name>`)")
        return 0
    for plugin in sorted(db.plugins.values(), key=lambda p: p.name):
        print(
            f"{plugin.name:20s} {plugin.version:12s} "
            f"{plugin.kind:11s} {plugin.source}"
        )
    return 0
