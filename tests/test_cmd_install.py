"""``flotilla install`` + composition unit tests.

These tests use a *local-source* plugin (passing a directory path as the
``--source``) so the installer never has to clone or pip-install. That
keeps unit tests fast and offline; the end-to-end test in
``test_e2e_hopewell.py`` exercises the pip path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flotilla.commands import cmd_init, cmd_install, cmd_list, cmd_remove


def _init(project: Path) -> None:
    cmd_init(argparse.Namespace(path=str(project), force=False))


def test_install_local_source_places_files(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin(
        "demo",
        agents={"demo-agent.md": "# Demo\nhello\n"},
        commands={"demo.md": "do the thing\n"},
    )
    rc = cmd_install(
        argparse.Namespace(
            names=["demo"],
            source=str(plugin),
            version="*",
            extras="",
            no_run_install=True,
        )
    )
    assert rc == 0
    placed = tmp_project / ".claude" / "agents" / "demo-agent.md"
    assert placed.exists()
    assert "hello" in placed.read_text(encoding="utf-8")
    assert (tmp_project / ".claude" / "commands" / "demo.md").exists()


def test_install_records_in_db(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "x"})
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    db = json.loads(
        (tmp_project / ".flotilla" / "installed.json").read_text(encoding="utf-8")
    )
    assert "demo" in db["plugins"]
    assert db["plugins"]["demo"]["version"] == "0.1.0"
    assert any("agents/a.md" in f for f in db["plugins"]["demo"]["contributed_files"])


def test_install_merges_settings_json(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin(
        "demo",
        hooks={
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo demo"}]}
                ]
            }
        },
    )
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    settings_path = tmp_project / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "flotilla:managed" in settings
    assert "demo" in settings["flotilla:managed"]
    assert "hooks" in settings
    assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Bash"


def test_install_preserves_user_settings(tmp_project: Path, make_plugin):
    _init(tmp_project)
    settings_path = tmp_project / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps({"theme": "dark", "hooks": {"PreToolUse": [{"matcher": "user"}]}}),
        encoding="utf-8",
    )
    plugin = make_plugin(
        "demo",
        hooks={"hooks": {"PreToolUse": [{"matcher": "demo"}]}},
    )
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["theme"] == "dark"
    matchers = [h.get("matcher") for h in settings["hooks"]["PreToolUse"]]
    assert "user" in matchers and "demo" in matchers


def test_install_then_list(tmp_project: Path, make_plugin, capsys):
    _init(tmp_project)
    plugin = make_plugin("demo", agents={"a.md": "x"})
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    rc = cmd_list(argparse.Namespace(format="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "demo" in out


def test_install_then_remove_cleans_up(tmp_project: Path, make_plugin):
    _init(tmp_project)
    plugin = make_plugin(
        "demo",
        kind="agent-pack",
        agents={"a.md": "x"},
        hooks={"hooks": {"PreToolUse": [{"matcher": "demo"}]}},
    )
    cmd_install(
        argparse.Namespace(
            names=["demo"], source=str(plugin), version="*", extras="",
            no_run_install=True,
        )
    )
    rc = cmd_remove(
        argparse.Namespace(
            name="demo", keep_pip=True, no_run_uninstall=True
        )
    )
    assert rc == 0
    assert not (tmp_project / ".claude" / "agents" / "a.md").exists()
    settings = json.loads(
        (tmp_project / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    assert "flotilla:managed" not in settings or "demo" not in settings.get(
        "flotilla:managed", {}
    )
