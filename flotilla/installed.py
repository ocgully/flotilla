"""On-disk record of installed plugins.

Lives at ``.flotilla/installed.json``. Records which plugins are
installed, where their plugin dir resolved to, and which files they
contributed to ``.claude/`` (so :func:`flotilla.compose.uninstall_plugin`
can clean up exactly what it placed and nothing more).

JSON because it's small, typed, and trivially git-diffable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InstalledPlugin:
    name: str
    version: str
    kind: str  # "tool" | "agent-pack"
    source: str  # "pip:<pkg>" or "git:<url>" or "path:<abs>"
    plugin_dir: str  # absolute path on disk to the plugin/ contents
    contributed_files: list[str] = field(default_factory=list)
    """Paths (relative to project root) that Flotilla placed for this plugin."""
    settings_keys: list[str] = field(default_factory=list)
    """Top-level ``.claude/settings.json`` keys this plugin contributed entries under."""


@dataclass
class InstalledDB:
    plugins: dict[str, InstalledPlugin] = field(default_factory=dict)

    def upsert(self, plugin: InstalledPlugin) -> None:
        self.plugins[plugin.name] = plugin

    def remove(self, name: str) -> InstalledPlugin | None:
        return self.plugins.pop(name, None)

    def get(self, name: str) -> InstalledPlugin | None:
        return self.plugins.get(name)


def load_db(path: Path) -> InstalledDB:
    if not path.exists():
        return InstalledDB()
    raw = json.loads(path.read_text(encoding="utf-8") or "{}")
    plugins = {}
    for name, p in (raw.get("plugins") or {}).items():
        plugins[name] = InstalledPlugin(
            name=p["name"],
            version=p.get("version", ""),
            kind=p.get("kind", "tool"),
            source=p.get("source", ""),
            plugin_dir=p.get("plugin_dir", ""),
            contributed_files=list(p.get("contributed_files") or []),
            settings_keys=list(p.get("settings_keys") or []),
        )
    return InstalledDB(plugins=plugins)


def save_db(db: InstalledDB, path: Path) -> None:
    payload: dict[str, Any] = {
        "plugins": {n: asdict(p) for n, p in db.plugins.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
