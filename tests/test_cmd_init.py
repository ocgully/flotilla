"""``flotilla init`` unit tests."""

from __future__ import annotations

import argparse
from pathlib import Path

from flotilla.commands import cmd_init


def test_init_creates_dirs_and_files(tmp_project: Path):
    args = argparse.Namespace(path=str(tmp_project), force=False)
    rc = cmd_init(args)
    assert rc == 0
    assert (tmp_project / ".flotilla").is_dir()
    assert (tmp_project / ".flotilla" / "manifest.yaml").is_file()
    assert (tmp_project / ".flotilla" / "config.yaml").is_file()
    assert (tmp_project / ".flotilla" / "cache").is_dir()


def test_init_idempotent(tmp_project: Path):
    args = argparse.Namespace(path=str(tmp_project), force=False)
    cmd_init(args)
    # Edit the manifest and re-run without --force; it should be preserved.
    manifest = tmp_project / ".flotilla" / "manifest.yaml"
    manifest.write_text("plugins:\n  - name: hopewell\n", encoding="utf-8")
    cmd_init(args)
    assert "hopewell" in manifest.read_text(encoding="utf-8")


def test_init_force_overwrites(tmp_project: Path):
    args = argparse.Namespace(path=str(tmp_project), force=False)
    cmd_init(args)
    manifest = tmp_project / ".flotilla" / "manifest.yaml"
    manifest.write_text("plugins:\n  - name: hopewell\n", encoding="utf-8")
    args = argparse.Namespace(path=str(tmp_project), force=True)
    cmd_init(args)
    assert "hopewell" not in manifest.read_text(encoding="utf-8")
