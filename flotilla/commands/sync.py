"""``flotilla sync`` — make on-disk state match ``.flotilla/manifest.yaml``."""

from __future__ import annotations

import argparse

from ..compose import install_plugin, uninstall_plugin
from ..config import load_config
from ..installed import load_db, save_db
from ..manifest import load_consumer_manifest
from ..paths import ProjectPaths, require_project_root
from ..resolve import ResolutionError, resolve


def cmd_sync(args: argparse.Namespace) -> int:
    project = ProjectPaths(root=require_project_root())
    config = load_config(project.config)
    db = load_db(project.installed_db)
    consumer = load_consumer_manifest(project.manifest)

    wanted = {p.name: p for p in consumer.plugins}
    have = set(db.plugins.keys())
    rc = 0

    # Remove orphans (installed but no longer in manifest)
    for orphan in sorted(have - set(wanted)):
        plugin = db.get(orphan)
        if plugin is not None:
            uninstall_plugin(plugin, project)
            db.remove(orphan)
            print(f"flotilla sync: removed orphan {orphan}")

    # Install or recompose declared plugins
    for name, entry in wanted.items():
        try:
            resolved = resolve(entry, cache_dir=project.cache)
        except ResolutionError as exc:
            print(f"flotilla sync {name}: {exc}")
            rc = 1
            continue
        existing = db.get(name)
        if existing:
            uninstall_plugin(existing, project)
        record = install_plugin(
            resolved.manifest,
            resolved.plugin_dir,
            project,
            config,
            source_descriptor=resolved.source_descriptor,
        )
        db.upsert(record)
        action = "synced" if existing else "installed"
        print(f"flotilla sync {name}: {action} ({resolved.manifest.version})")

    save_db(db, project.installed_db)
    return rc
