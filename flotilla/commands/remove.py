"""``flotilla remove`` — uninstall a plugin."""

from __future__ import annotations

import argparse

from ..compose import uninstall_plugin
from ..installed import load_db, save_db
from ..manifest import load_consumer_manifest, write_consumer_manifest
from ..paths import ProjectPaths, require_project_root
from ..resolve import PipRunner
from ..registry import lookup
from .install import _run_step


def cmd_remove(args: argparse.Namespace) -> int:
    project = ProjectPaths(root=require_project_root())
    db = load_db(project.installed_db)
    consumer = load_consumer_manifest(project.manifest)
    plugin = db.get(args.name)
    if plugin is None:
        print(f"flotilla remove {args.name}: not installed")
        return 1

    removed = uninstall_plugin(plugin, project)
    db.remove(args.name)
    save_db(db, project.installed_db)

    consumer.plugins = [p for p in consumer.plugins if p.name != args.name]
    write_consumer_manifest(consumer, project.manifest)

    # Run on_uninstall (read manifest from the plugin dir if it still exists).
    if not args.no_run_uninstall:
        manifest_path = (
            __import__("pathlib").Path(plugin.plugin_dir).parent / "flotilla.yaml"
        )
        if manifest_path.exists():
            from ..manifest import load_plugin_manifest

            manifest = load_plugin_manifest(manifest_path)
            for step in manifest.on_uninstall:
                _run_step(step, cwd=project.root)

    if plugin.kind == "tool" and not args.keep_pip:
        known = lookup(plugin.name)
        pkg = (known.pip_package if known else None) or plugin.name
        try:
            PipRunner().uninstall(pkg)
        except Exception as exc:
            print(f"flotilla: pip uninstall {pkg} failed (continuing): {exc}")

    print(f"flotilla remove {args.name}: removed {len(removed)} files")
    return 0
