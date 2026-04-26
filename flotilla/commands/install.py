"""``flotilla install`` — resolve, compose, run on_install."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from pathlib import Path

from ..compose import install_plugin
from ..config import load_config
from ..installed import load_db, save_db
from ..manifest import (
    ConsumerPluginEntry,
    load_consumer_manifest,
    write_consumer_manifest,
)
from ..paths import ProjectPaths, require_project_root
from ..resolve import ResolutionError, resolve


def cmd_install(args: argparse.Namespace) -> int:
    root = require_project_root()
    project = ProjectPaths(root=root)
    config = load_config(project.config)
    db = load_db(project.installed_db)
    consumer = load_consumer_manifest(project.manifest)

    extras = (
        [e.strip() for e in args.extras.split(",") if e.strip()]
        if args.extras
        else []
    )

    if args.source and len(args.names) != 1:
        raise SystemExit(
            "flotilla install: --source can only be used with a single plugin name"
        )

    rc = 0
    for name in args.names:
        entry = consumer.find(name)
        if entry is None:
            entry = ConsumerPluginEntry(
                name=name,
                version=args.version,
                source=args.source if args.source and len(args.names) == 1 else None,
                extras=list(extras),
            )
            consumer.plugins.append(entry)
        else:
            if args.version != "*":
                entry.version = args.version
            if args.source and len(args.names) == 1:
                entry.source = args.source
            if extras:
                entry.extras = list(extras)

        try:
            resolved = resolve(entry, cache_dir=project.cache)
        except ResolutionError as exc:
            print(f"flotilla install {name}: {exc}")
            rc = 1
            continue

        record = install_plugin(
            resolved.manifest,
            resolved.plugin_dir,
            project,
            config,
            source_descriptor=resolved.source_descriptor,
        )
        db.upsert(record)
        save_db(db, project.installed_db)

        if not args.no_run_install:
            for step in resolved.manifest.on_install:
                _run_step(step, cwd=project.root)

        print(
            f"flotilla install {name}: {resolved.manifest.version} "
            f"({len(record.contributed_files)} files placed, "
            f"settings keys: {', '.join(record.settings_keys) or 'none'})"
        )

    write_consumer_manifest(consumer, project.manifest)
    return rc


def _run_step(step: str, cwd: Path) -> None:
    """Best-effort run of an on_install / on_uninstall shell step.

    Failure is printed but doesn't abort the install — these are
    convenience steps (hooks install, store init), not correctness
    gates. The user can re-run them manually from the README.
    """

    print(f"flotilla: running on_install: {step}")
    try:
        if os.name == "nt":
            # Use shell on Windows so bare taskflow/pedia entrypoints resolve.
            subprocess.run(step, cwd=cwd, shell=True, check=False)
        else:
            subprocess.run(shlex.split(step), cwd=cwd, check=False)
    except OSError as exc:
        print(f"flotilla: on_install step failed (continuing): {exc}")
