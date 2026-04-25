"""``flotilla upgrade``, ``sync``, ``validate``, ``doctor`` unit tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flotilla.commands import (
    cmd_doctor,
    cmd_init,
    cmd_install,
    cmd_sync,
    cmd_upgrade,
    cmd_validate,
)


def _init(p: Path) -> None:
    cmd_init(argparse.Namespace(path=str(p), force=False))


def test_validate_ok_and_bad(tmp_path: Path, make_plugin, capsys):
    good = make_plugin("good", agents={"a.md": "x"})
    rc = cmd_validate(argparse.Namespace(path=str(good)))
    assert rc == 0
    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "flotilla.yaml").write_text(
        "name: bad\nversion: \"0.1\"\nkind: tool\ncontributes:\n  agents: missing/\n",
        encoding="utf-8",
    )
    # The plugin/ dir is also missing — validate reports both.
    # (validate looks for plugin/ directory regardless of contributions.)
    rc = cmd_validate(argparse.Namespace(path=str(bad_dir)))
    assert rc == 1
    out = capsys.readouterr().out
    assert "missing" in out


def test_upgrade_recomposes(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "v1\n"})
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    placed = tmp_project / ".claude" / "agents" / "a.md"
    assert "v1" in placed.read_text(encoding="utf-8")

    # Bump the plugin in-place.
    (plugin / "plugin" / "agents" / "a.md").write_text("v2\n", encoding="utf-8")
    (plugin / "flotilla.yaml").write_text(
        "name: demo\nversion: 0.2.0\nkind: tool\ncontributes:\n  agents: plugin/agents/\n",
        encoding="utf-8",
    )
    rc = cmd_upgrade(argparse.Namespace(name="demo"))
    assert rc == 0
    assert "v2" in placed.read_text(encoding="utf-8")


def test_sync_installs_declared(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "x"})
    # Hand-edit the manifest to declare a plugin (with a source path so
    # the resolver can find it).
    manifest = tmp_project / ".flotilla" / "manifest.yaml"
    manifest.write_text(
        f"plugins:\n  - name: demo\n    version: \"*\"\n    source: \"{plugin.as_posix()}\"\n",
        encoding="utf-8",
    )
    rc = cmd_sync(argparse.Namespace())
    assert rc == 0
    assert (tmp_project / ".claude" / "agents" / "a.md").exists()


def test_sync_removes_orphans(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "x"})
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    # Wipe the manifest and re-sync — should remove the orphan.
    manifest = tmp_project / ".flotilla" / "manifest.yaml"
    manifest.write_text("plugins: []\n", encoding="utf-8")
    rc = cmd_sync(argparse.Namespace())
    assert rc == 0
    assert not (tmp_project / ".claude" / "agents" / "a.md").exists()


def test_doctor_clean(tmp_project: Path, make_plugin, capsys):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "x"})
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    rc = cmd_doctor(argparse.Namespace())
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_doctor_detects_missing_file(tmp_project: Path, make_plugin, capsys):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "x"})
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    (tmp_project / ".claude" / "agents" / "a.md").unlink()
    rc = cmd_doctor(argparse.Namespace())
    assert rc == 1
    assert "missing contributed file" in capsys.readouterr().out
