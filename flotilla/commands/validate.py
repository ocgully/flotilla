"""``flotilla validate`` — check a plugin repo's manifest for correctness."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..manifest import ManifestError, load_plugin_manifest


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path).resolve()
    manifest_path = path / "flotilla.yaml" if path.is_dir() else path
    if not manifest_path.exists():
        print(f"flotilla validate: no flotilla.yaml at {manifest_path}")
        return 1
    try:
        manifest = load_plugin_manifest(manifest_path)
    except ManifestError as exc:
        print(f"flotilla validate: {exc}")
        return 1
    plugin_dir = manifest_path.parent / manifest.plugin_dir_default
    issues: list[str] = []
    if not plugin_dir.is_dir():
        issues.append(f"missing plugin/ directory at {plugin_dir}")
    c = manifest.contributes
    for label, sub in (
        ("agents", c.agents),
        ("skills", c.skills),
        ("commands", c.commands),
    ):
        if sub:
            full = manifest_path.parent / sub
            if not full.is_dir():
                issues.append(f"contributes.{label} -> {full} (not a directory)")
    for label, sub in (("hooks", c.hooks), ("mcp", c.mcp)):
        if sub:
            full = manifest_path.parent / sub
            if not full.is_file():
                issues.append(f"contributes.{label} -> {full} (not a file)")
    if issues:
        print(f"flotilla validate: {manifest_path} has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(
        f"flotilla validate: OK — {manifest.name} {manifest.version} "
        f"(kind={manifest.kind}, "
        f"{'pip' if manifest.is_pip_plugin else 'git-clone'})"
    )
    return 0
