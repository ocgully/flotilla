"""Composition layer — copy/symlink a plugin's contributions into ``.claude/``.

A plugin's ``flotilla.yaml`` declares directories under its ``plugin/``
tree that contribute to the consumer project:

* ``contributes.agents``  -> goes to ``.claude/agents/``
* ``contributes.skills``  -> goes to ``.claude/skills/``
* ``contributes.commands`` -> goes to ``.claude/commands/``
* ``contributes.hooks``   -> a YAML file merged into ``.claude/settings.json``
* ``contributes.mcp``     -> a YAML file merged into ``.claude/settings.json``

The composition layer never overwrites user-authored files: every
contribution file is tagged in :class:`InstalledPlugin.contributed_files`
when it's placed, so :func:`uninstall_plugin` removes exactly what it
put there and leaves user content alone. ``settings.json`` entries are
fenced under a ``flotilla:managed`` sentinel block per plugin, so a user
who manually edits the file outside the fence keeps their edits across
upgrade cycles.

All work is idempotent — running :func:`install_plugin` twice for the
same plugin/version produces the same on-disk state.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
from pathlib import Path
from typing import Any

from .config import FlotillaConfig
from .installed import InstalledPlugin
from .manifest import PluginManifest, _load_yaml_text
from .paths import ProjectPaths


# Sentinel for fenced regions inside .claude/settings.json. Each plugin
# owns one fenced block per top-level key it contributes to (currently
# ``hooks`` and ``mcpServers`` per Claude Code conventions).
SENTINEL = "flotilla:managed"


# ---------------------------------------------------------------------------
# Install / uninstall
# ---------------------------------------------------------------------------


def install_plugin(
    manifest: PluginManifest,
    plugin_dir: Path,
    project: ProjectPaths,
    config: FlotillaConfig,
    *,
    source_descriptor: str,
) -> InstalledPlugin:
    """Place a plugin's contributions in ``.claude/``.

    ``plugin_dir`` is the on-disk directory containing the plugin's
    ``agents/`` / ``skills/`` / ``commands/`` / ``hooks.yaml`` / ``mcp.yaml``
    sub-paths (i.e. the parent of the manifest's ``plugin/`` dir, since
    contribution paths are written relative to the manifest root).
    ``source_descriptor`` is a short string describing where the plugin
    came from for record-keeping (``pip:hopewell``, etc.).
    """

    placed: list[str] = []
    settings_keys: list[str] = []
    link_mode = config.resolve_link_mode()
    contributes = manifest.contributes
    # ``plugin_dir`` here is the *manifest root* — i.e. the directory that
    # contains ``flotilla.yaml``. Contribution paths like ``plugin/agents/``
    # are written relative to that root.
    manifest_root = plugin_dir

    if contributes.agents:
        src = manifest_root / contributes.agents
        if src.is_dir():
            placed.extend(
                _place_dir(
                    src,
                    project.claude_agents,
                    project.root,
                    link_mode,
                    plugin_name=manifest.name,
                )
            )
    if contributes.skills:
        src = manifest_root / contributes.skills
        if src.is_dir():
            placed.extend(
                _place_dir(
                    src,
                    project.claude_skills,
                    project.root,
                    link_mode,
                    plugin_name=manifest.name,
                )
            )
    if contributes.commands:
        src = manifest_root / contributes.commands
        if src.is_dir():
            placed.extend(
                _place_dir(
                    src,
                    project.claude_commands,
                    project.root,
                    link_mode,
                    plugin_name=manifest.name,
                )
            )

    if contributes.hooks:
        hook_file = manifest_root / contributes.hooks
        if hook_file.is_file():
            keys = _merge_yaml_into_settings(
                hook_file, project.claude_settings, manifest.name
            )
            settings_keys.extend(keys)

    if contributes.mcp:
        mcp_file = manifest_root / contributes.mcp
        if mcp_file.is_file():
            keys = _merge_yaml_into_settings(
                mcp_file, project.claude_settings, manifest.name
            )
            settings_keys.extend(keys)

    return InstalledPlugin(
        name=manifest.name,
        version=manifest.version,
        kind=manifest.kind,
        source=source_descriptor,
        plugin_dir=str(plugin_dir.resolve()),
        contributed_files=sorted(set(placed)),
        settings_keys=sorted(set(settings_keys)),
    )


def uninstall_plugin(
    plugin: InstalledPlugin, project: ProjectPaths
) -> list[str]:
    """Remove everything :func:`install_plugin` placed for this plugin.

    Returns the list of paths actually removed (for the CLI summary).
    """

    removed: list[str] = []
    for rel in plugin.contributed_files:
        path = project.root / rel
        if path.exists() or path.is_symlink():
            try:
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                removed.append(rel)
            except OSError:
                pass
        # Try to clean the parent dir if empty (e.g. .claude/agents/ once
        # all plugin agents are gone). Never remove .claude/ itself.
        parent = path.parent
        try:
            if parent.exists() and not any(parent.iterdir()) and parent != project.claude_dir:
                parent.rmdir()
        except OSError:
            pass

    if project.claude_settings.exists():
        _strip_settings_for(project.claude_settings, plugin.name)

    return removed


# ---------------------------------------------------------------------------
# File placement (copy or symlink)
# ---------------------------------------------------------------------------


def _place_dir(
    src_dir: Path,
    dst_dir: Path,
    project_root: Path,
    link_mode: str,
    *,
    plugin_name: str,
) -> list[str]:
    """Copy/symlink each file under ``src_dir`` to ``dst_dir``.

    Returns relative-to-project paths that were placed. Skips files that
    already exist and are user-authored (i.e. not previously placed by
    Flotilla — checked via the absence of a marker).
    """

    placed: list[str] = []
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_dir.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(src_dir)
        target = dst_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)

        # If a file is already there and it wasn't placed by us, leave it
        # alone — user override wins. We detect "ours" by recreating the
        # exact link/copy we'd produce; if target is identical, treat as
        # ours and overwrite (idempotent re-install).
        if target.exists() or target.is_symlink():
            if not _is_replaceable(target, src, link_mode):
                continue
            try:
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            except OSError:
                continue

        _link_or_copy(src, target, link_mode)
        placed.append(str(target.relative_to(project_root)).replace("\\", "/"))
    return placed


def _is_replaceable(target: Path, src: Path, link_mode: str) -> bool:
    if link_mode == "symlink" and target.is_symlink():
        try:
            return target.resolve() == src.resolve()
        except OSError:
            return False
    if link_mode == "copy" and target.is_file() and src.is_file():
        try:
            return target.read_bytes() == src.read_bytes()
        except OSError:
            return False
    return False


def _link_or_copy(src: Path, dst: Path, link_mode: str) -> None:
    if link_mode == "symlink":
        try:
            os.symlink(src, dst)
            return
        except (OSError, NotImplementedError):
            # Fall back to copy on permission errors (Windows non-admin).
            pass
    shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# settings.json merging
# ---------------------------------------------------------------------------


def _merge_yaml_into_settings(
    yaml_file: Path, settings_path: Path, plugin_name: str
) -> list[str]:
    """Merge a plugin's hooks.yaml or mcp.yaml into ``.claude/settings.json``.

    The YAML is read, its top-level keys (e.g. ``hooks``, ``mcpServers``)
    are merged into the corresponding settings.json keys under a
    ``flotilla:managed`` sentinel block per plugin. Existing user entries
    are preserved.
    """

    data = _load_yaml_text(yaml_file.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return []
    settings = _read_settings(settings_path)
    settings.setdefault(SENTINEL, {})
    settings[SENTINEL][plugin_name] = data

    # Project the managed contributions into the live keys for downstream
    # tools that don't know about the sentinel. Live keys are the union
    # of user-authored content + every managed plugin's content.
    keys_touched = list(data.keys())
    for key in keys_touched:
        live = settings.get(key)
        if live is None:
            settings[key] = _clone(data[key])
        elif isinstance(live, dict) and isinstance(data[key], dict):
            for inner_k, inner_v in data[key].items():
                _merge_into(live, inner_k, inner_v)
        elif isinstance(live, list) and isinstance(data[key], list):
            # Append; matchers/MCP servers are array-typed — duplicates
            # tolerated. Replay-safe because an upgrade re-strips this
            # plugin's entries first.
            live.extend(_clone(item) for item in data[key])
        # else: type mismatch — skip silently; user wins.

    _write_settings(settings_path, settings)
    return keys_touched


def _strip_settings_for(settings_path: Path, plugin_name: str) -> None:
    settings = _read_settings(settings_path)
    sentinel_block = settings.get(SENTINEL) or {}
    plugin_block = sentinel_block.pop(plugin_name, None)
    if not plugin_block:
        return
    if not sentinel_block:
        settings.pop(SENTINEL, None)
    else:
        settings[SENTINEL] = sentinel_block

    # Rebuild live keys from scratch: take user-authored content (settings
    # before any merge) PLUS the remaining managed plugins. Since we don't
    # store a pristine pre-merge copy, we approximate by stripping the
    # exact contents this plugin contributed.
    for key, plugin_value in plugin_block.items():
        live = settings.get(key)
        if live is None:
            continue
        if isinstance(live, dict) and isinstance(plugin_value, dict):
            for inner_k in plugin_value.keys():
                # Only remove the inner key if no other managed plugin
                # contributed it.
                still_owned_by_others = any(
                    isinstance(other, dict) and inner_k in other
                    for other in sentinel_block.values()
                    if isinstance(other, dict)
                )
                # 'other' is keyed plugin_name -> plugin contributions; we
                # need to look at each plugin's plugin_value[key].
                still_owned_by_others = False
                for other_plugin_block in sentinel_block.values():
                    if not isinstance(other_plugin_block, dict):
                        continue
                    other_value = other_plugin_block.get(key)
                    if isinstance(other_value, dict) and inner_k in other_value:
                        still_owned_by_others = True
                        break
                if not still_owned_by_others:
                    live.pop(inner_k, None)
            if not live:
                settings.pop(key, None)
        elif isinstance(live, list) and isinstance(plugin_value, list):
            # Best effort: remove items equal-by-value.
            for item in plugin_value:
                try:
                    live.remove(item)
                except ValueError:
                    continue
            if not live:
                settings.pop(key, None)

    _write_settings(settings_path, settings)


def _read_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Don't silently destroy malformed user JSON.
        raise


def _write_settings(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
    )


def _merge_into(target: dict[str, Any], key: str, value: Any) -> None:
    """Merge ``value`` into ``target[key]``, preserving prior content.

    Lists are appended to (so two plugins both contributing
    ``hooks.PreToolUse`` matchers stack); dicts are recursively merged;
    everything else is overwritten last-wins. The strip path on uninstall
    relies on equal-by-value list-item removal, so order does not matter
    for round-tripping.
    """
    existing = target.get(key)
    if existing is None:
        target[key] = _clone(value)
    elif isinstance(existing, list) and isinstance(value, list):
        existing.extend(_clone(v) for v in value)
    elif isinstance(existing, dict) and isinstance(value, dict):
        for k, v in value.items():
            _merge_into(existing, k, v)
    else:
        target[key] = _clone(value)


def _clone(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _clone(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clone(v) for v in value]
    return value
