"""Path discovery utilities — finds the project root and Flotilla dirs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectPaths:
    """Standard layout for a Flotilla-managed project."""

    root: Path

    @property
    def flotilla_dir(self) -> Path:
        return self.root / ".flotilla"

    @property
    def manifest(self) -> Path:
        return self.flotilla_dir / "manifest.yaml"

    @property
    def config(self) -> Path:
        return self.flotilla_dir / "config.yaml"

    @property
    def lock(self) -> Path:
        return self.flotilla_dir / "resolved.lock"

    @property
    def cache(self) -> Path:
        return self.flotilla_dir / "cache"

    @property
    def installed_db(self) -> Path:
        return self.flotilla_dir / "installed.json"

    @property
    def claude_dir(self) -> Path:
        return self.root / ".claude"

    @property
    def claude_agents(self) -> Path:
        return self.claude_dir / "agents"

    @property
    def claude_skills(self) -> Path:
        return self.claude_dir / "skills"

    @property
    def claude_commands(self) -> Path:
        return self.claude_dir / "commands"

    @property
    def claude_settings(self) -> Path:
        return self.claude_dir / "settings.json"


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk upward looking for a ``.flotilla/`` directory.

    Returns ``None`` if no Flotilla project is found. Callers typically
    call :func:`require_project_root` instead.
    """

    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / ".flotilla").is_dir():
            return candidate
    return None


def require_project_root(start: Path | None = None) -> Path:
    """Like :func:`find_project_root` but raises if the project is unfound."""
    root = find_project_root(start)
    if root is None:
        raise SystemExit(
            "flotilla: no .flotilla/ directory found. Run `flotilla init` first."
        )
    return root
