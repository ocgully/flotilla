"""Per-project Flotilla configuration.

Sits at ``.flotilla/config.yaml`` and controls how Flotilla composes
contributions into ``.claude/`` for this project. Distinct from the
manifest (which lists *what* to install); this controls *how*.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import _dump_yaml, _load_yaml_text


@dataclass
class FlotillaConfig:
    link_mode: str = "auto"
    """One of ``auto``, ``copy``, ``symlink``.

    On Windows the default ``auto`` resolves to ``copy`` because reliable
    symlinks require admin / dev mode. POSIX ``auto`` resolves to
    ``symlink``. Users can opt into either explicitly via this field.
    """

    cache_dir: str = ".flotilla/cache"
    """Where git-clone plugins are cached (relative to project root)."""

    def resolve_link_mode(self) -> str:
        if self.link_mode != "auto":
            return self.link_mode
        return "copy" if platform.system() == "Windows" else "symlink"


def load_config(path: Path) -> FlotillaConfig:
    if not path.exists():
        return FlotillaConfig()
    raw = _load_yaml_text(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return FlotillaConfig()
    link_mode = raw.get("link_mode", "auto")
    if link_mode not in ("auto", "copy", "symlink"):
        link_mode = "auto"
    cache_dir = raw.get("cache_dir") or ".flotilla/cache"
    return FlotillaConfig(link_mode=link_mode, cache_dir=str(cache_dir))


def write_config(cfg: FlotillaConfig, path: Path) -> None:
    payload: dict[str, Any] = {
        "link_mode": cfg.link_mode,
        "cache_dir": cfg.cache_dir,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(payload), encoding="utf-8")
