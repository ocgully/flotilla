"""``flotilla init`` — scaffold a project for plugin installation."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..config import FlotillaConfig, write_config
from ..manifest import ConsumerManifest, write_consumer_manifest
from ..paths import ProjectPaths


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    project = ProjectPaths(root=root)
    project.flotilla_dir.mkdir(parents=True, exist_ok=True)
    project.cache.mkdir(parents=True, exist_ok=True)

    if not project.manifest.exists() or args.force:
        write_consumer_manifest(ConsumerManifest(plugins=[]), project.manifest)
    if not project.config.exists() or args.force:
        write_config(FlotillaConfig(), project.config)

    print(f"flotilla: initialised {project.flotilla_dir}")
    print(f"  manifest: {project.manifest}")
    print(f"  config:   {project.config}")
    print(
        "Next: `flotilla install <plugin>` (try taskflow, pedia, codeatlas, diffsextant, slim-agents)"
    )
    return 0
