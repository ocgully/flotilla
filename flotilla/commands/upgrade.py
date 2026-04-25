"""``flotilla upgrade`` — re-resolve + recompose installed plugins."""

from __future__ import annotations

import argparse

from ..compose import install_plugin, uninstall_plugin
from ..config import load_config
from ..installed import load_db, save_db
from ..manifest import load_consumer_manifest
from ..paths import ProjectPaths, require_project_root
from ..resolve import ResolutionError, resolve


def cmd_upgrade(args: argparse.Namespace) -> int:
    project = ProjectPaths(root=require_project_root())
    config = load_config(project.config)
    db = load_db(project.installed_db)
    consumer = load_consumer_manifest(project.manifest)

    targets = [args.name] if args.name else list(db.plugins.keys())
    if not targets:
        print("flotilla: nothing to upgrade")
        return 0

    rc = 0
    for name in targets:
        existing = db.get(name)
        entry = consumer.find(name)
        if existing is None:
            print(f"flotilla upgrade {name}: not installed")
            rc = 1
            continue
        if entry is None:
            print(f"flotilla upgrade {name}: not in .flotilla/manifest.yaml")
            rc = 1
            continue
        try:
            resolved = resolve(entry, cache_dir=project.cache)
        except ResolutionError as exc:
            print(f"flotilla upgrade {name}: {exc}")
            rc = 1
            continue
        # Re-compose: strip what was placed before, then place fresh files.
        uninstall_plugin(existing, project)
        record = install_plugin(
            resolved.manifest,
            resolved.plugin_dir,
            project,
            config,
            source_descriptor=resolved.source_descriptor,
        )
        db.upsert(record)
        save_db(db, project.installed_db)
        print(
            f"flotilla upgrade {name}: "
            f"{existing.version} -> {resolved.manifest.version}"
        )
    return rc
