"""Shared pytest fixtures for Flotilla tests.

Most tests build a fake plugin in a tmp directory + a fake project also
in a tmp directory and exercise the CLI sub-commands directly. The
:func:`make_plugin` fixture writes a minimal-but-realistic plugin tree
with all the contribution types (agents/skills/commands/hooks/mcp) so
tests can pick the slice they need.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A pristine project root with cwd set to it."""
    proj = tmp_path / "project"
    proj.mkdir()
    monkeypatch.chdir(proj)
    return proj


@pytest.fixture
def make_plugin(tmp_path: Path):
    """Factory that writes a fake plugin repo at ``tmp_path/<name>``."""

    def _make(
        name: str,
        *,
        version: str = "0.1.0",
        kind: str = "tool",
        with_pip: bool = False,
        agents: dict[str, str] | None = None,
        skills: dict[str, str] | None = None,
        commands: dict[str, str] | None = None,
        hooks: dict | None = None,
        mcp: dict | None = None,
        on_install: list[str] | None = None,
    ) -> Path:
        repo = tmp_path / name
        repo.mkdir()
        plug = repo / "plugin"
        plug.mkdir()
        if agents:
            (plug / "agents").mkdir()
            for fn, body in agents.items():
                (plug / "agents" / fn).write_text(body, encoding="utf-8")
        if skills:
            (plug / "skills").mkdir()
            for fn, body in skills.items():
                (plug / "skills" / fn).write_text(body, encoding="utf-8")
        if commands:
            (plug / "commands").mkdir()
            for fn, body in commands.items():
                (plug / "commands" / fn).write_text(body, encoding="utf-8")
        if hooks is not None:
            (plug / "hooks.yaml").write_text(_dump(hooks), encoding="utf-8")
        if mcp is not None:
            (plug / "mcp.yaml").write_text(_dump(mcp), encoding="utf-8")

        manifest_lines = [
            f"name: {name}",
            f"version: {version}",
            f"kind: {kind}",
            "contributes:",
        ]
        if agents:
            manifest_lines.append("  agents: plugin/agents/")
        if skills:
            manifest_lines.append("  skills: plugin/skills/")
        if commands:
            manifest_lines.append("  commands: plugin/commands/")
        if hooks is not None:
            manifest_lines.append("  hooks: plugin/hooks.yaml")
        if mcp is not None:
            manifest_lines.append("  mcp: plugin/mcp.yaml")
        if with_pip:
            manifest_lines += [
                "python_package:",
                f"  name: {name}",
                "  extras: []",
            ]
        if on_install:
            manifest_lines.append("on_install:")
            for step in on_install:
                manifest_lines.append(f"  - {step}")
        (repo / "flotilla.yaml").write_text(
            "\n".join(manifest_lines) + "\n", encoding="utf-8"
        )
        return repo

    return _make


def _dump(data) -> str:
    """Tiny YAML emitter used by tests when PyYAML may be absent."""
    try:
        import yaml  # type: ignore

        return yaml.safe_dump(data, sort_keys=False)
    except ImportError:
        from flotilla.manifest import _dump_yaml

        return _dump_yaml(data)
