"""``flotilla doctor`` — diagnose project + plugin health."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..config import load_config
from ..installed import load_db
from ..manifest import load_consumer_manifest
from ..paths import ProjectPaths, require_project_root


def cmd_doctor(args: argparse.Namespace) -> int:
    project = ProjectPaths(root=require_project_root())
    db = load_db(project.installed_db)
    consumer = load_consumer_manifest(project.manifest)

    issues: list[str] = []
    if not project.flotilla_dir.exists():
        issues.append(".flotilla/ missing — run `flotilla init`")
    if not project.manifest.exists():
        issues.append(
            f"{project.manifest} missing — re-run `flotilla init` to recreate"
        )
    if not project.config.exists():
        issues.append(
            f"{project.config} missing — re-run `flotilla init` to recreate"
        )

    declared = {p.name for p in consumer.plugins}
    installed = set(db.plugins.keys())
    for missing in sorted(declared - installed):
        issues.append(f"declared but not installed: {missing} — run `flotilla sync`")
    for orphan in sorted(installed - declared):
        issues.append(f"installed but not declared: {orphan} — run `flotilla sync`")

    for name, plugin in db.plugins.items():
        for rel in plugin.contributed_files:
            target = project.root / rel
            if not target.exists() and not target.is_symlink():
                issues.append(f"{name}: missing contributed file {rel}")
        plugin_dir = Path(plugin.plugin_dir)
        if not plugin_dir.exists():
            issues.append(
                f"{name}: plugin dir gone ({plugin_dir}) — run `flotilla upgrade {name}`"
            )

    link_mode = (
        load_config(project.config).resolve_link_mode()
        if project.config.exists()
        else "auto"
    )
    if issues:
        print(f"flotilla doctor: {len(issues)} issue(s) found")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(
        f"flotilla doctor: OK ({len(installed)} plugin(s), link mode = {link_mode})"
    )
    return 0
