"""Manifest schema + parser/validator for Flotilla.

Two manifest shapes share this module:

1. **Plugin manifest** — a plugin's repo root contains ``flotilla.yaml``
   declaring its name, version, contributions, and on_install steps.
2. **Consumer manifest** — a project consuming plugins keeps
   ``.flotilla/manifest.yaml`` listing which plugins it installs.

Both are validated by :func:`load_plugin_manifest` /
:func:`load_consumer_manifest`. Errors are raised as
:class:`ManifestError` with a human-readable message that names the file
and the offending field, so CLI users see exactly what to fix.

YAML parsing falls back to a tiny pure-Python loader when PyYAML is not
installed. The loader supports the strict subset used by Flotilla
manifests (mappings, lists, scalars, comments, double-/single-quoted
strings) — enough for self-test, but PyYAML is recommended for
production. Plugins free to use any YAML they like; the fallback is
opt-in by absence of PyYAML.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ManifestError(ValueError):
    """Raised when a manifest fails to parse or validate."""


# ---------------------------------------------------------------------------
# YAML loading — PyYAML if present, otherwise a tiny built-in loader.
# ---------------------------------------------------------------------------


def _load_yaml_text(text: str) -> Any:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        return _mini_yaml_load(text)


def _mini_yaml_load(text: str) -> Any:
    """Pure-Python YAML loader for the strict subset used by manifests.

    Supports:
      * Mappings with ``key: value`` (string keys only)
      * Lists with ``- item`` syntax (also ``- key: value`` for list-of-mappings)
      * Scalars: int, float, bool, null, single-/double-quoted strings, bare
      * Comments after ``#``
      * Blank lines

    Does NOT support: flow-style ``{a: b}`` / ``[a, b]``, anchors, multi-line
    folded scalars, custom tags. If you need those, install PyYAML.
    """

    lines = text.splitlines()
    # Strip comments + blank lines but preserve indentation.
    cleaned: list[tuple[int, str]] = []
    for raw in lines:
        stripped = _strip_yaml_comment(raw).rstrip()
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        cleaned.append((indent, stripped[indent:]))

    parsed, _ = _parse_block(cleaned, 0, 0)
    return parsed


def _strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _parse_block(
    items: list[tuple[int, str]], pos: int, indent: int
) -> tuple[Any, int]:
    if pos >= len(items):
        return None, pos
    first_indent, first_text = items[pos]
    if first_indent < indent:
        return None, pos
    if first_text.startswith("- "):
        return _parse_list(items, pos, first_indent)
    return _parse_mapping(items, pos, first_indent)


def _parse_mapping(
    items: list[tuple[int, str]], pos: int, indent: int
) -> tuple[dict, int]:
    out: dict[str, Any] = {}
    while pos < len(items):
        i, text = items[pos]
        if i < indent:
            break
        if i > indent:
            raise ManifestError(f"unexpected indent at: {text!r}")
        if ":" not in text:
            raise ManifestError(f"expected 'key: value' but got: {text!r}")
        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        pos += 1
        if value:
            out[key] = _parse_scalar(value)
        else:
            child, pos = _parse_block(items, pos, indent + 1)
            out[key] = child if child is not None else {}
    return out, pos


def _parse_list(
    items: list[tuple[int, str]], pos: int, indent: int
) -> tuple[list, int]:
    out: list[Any] = []
    while pos < len(items):
        i, text = items[pos]
        if i < indent or not text.startswith("- "):
            break
        if i > indent:
            raise ManifestError(f"unexpected indent at: {text!r}")
        body = text[2:].strip()
        pos += 1
        if ":" in body and not _looks_quoted(body):
            # list-of-mappings — first key:val is the head, rest at indent+2
            key, _, value = body.partition(":")
            key = key.strip()
            value = value.strip()
            mapping: dict[str, Any] = {}
            if value:
                mapping[key] = _parse_scalar(value)
            else:
                child, pos = _parse_block(items, pos, indent + 2)
                mapping[key] = child if child is not None else {}
            # parse remaining keys of this mapping at indent+2
            while pos < len(items):
                ni, ntext = items[pos]
                if ni < indent + 2 or ntext.startswith("- "):
                    break
                if ni > indent + 2:
                    raise ManifestError(f"unexpected indent at: {ntext!r}")
                if ":" not in ntext:
                    raise ManifestError(
                        f"expected 'key: value' in list mapping: {ntext!r}"
                    )
                k2, _, v2 = ntext.partition(":")
                k2 = k2.strip()
                v2 = v2.strip()
                pos += 1
                if v2:
                    mapping[k2] = _parse_scalar(v2)
                else:
                    child, pos = _parse_block(items, pos, indent + 4)
                    mapping[k2] = child if child is not None else {}
            out.append(mapping)
        else:
            out.append(_parse_scalar(body))
    return out, pos


def _looks_quoted(s: str) -> bool:
    return (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    )


def _parse_scalar(s: str) -> Any:
    s = s.strip()
    if not s:
        return None
    if s in ("null", "~", "None"):
        return None
    if s in ("true", "True", "yes"):
        return True
    if s in ("false", "False", "no"):
        return False
    if _looks_quoted(s):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p.strip()) for p in inner.split(",")]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _dump_yaml(data: Any) -> str:
    """Tiny YAML emitter for the manifest subset. Used when PyYAML is absent."""
    try:
        import yaml  # type: ignore

        return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    except ImportError:
        lines: list[str] = []
        _emit(data, lines, 0)
        return "\n".join(lines) + "\n"


def _emit(value: Any, out: list[str], indent: int) -> None:
    pad = "  " * indent
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:")
                _emit(v, out, indent + 1)
            else:
                out.append(f"{pad}{k}: {_emit_scalar(v)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    if isinstance(v, (dict, list)) and v:
                        out.append(f"{prefix}{k}:")
                        _emit(v, out, indent + 2)
                    else:
                        out.append(f"{prefix}{k}: {_emit_scalar(v)}")
                    first = False
            else:
                out.append(f"{pad}- {_emit_scalar(item)}")


def _emit_scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or any(c in s for c in ":#\n") or s.strip() != s:
        return '"' + s.replace('"', '\\"') + '"'
    return s


# ---------------------------------------------------------------------------
# Plugin manifest (lives in plugin repo root as flotilla.yaml)
# ---------------------------------------------------------------------------


_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


@dataclass
class PluginContributes:
    agents: str | None = None
    skills: str | None = None
    commands: str | None = None
    hooks: str | None = None
    mcp: str | None = None


@dataclass
class PythonPackage:
    name: str
    extras: list[str] = field(default_factory=list)


@dataclass
class PluginManifest:
    """Plugin-side manifest: the plugin author's declaration of contributions."""

    name: str
    version: str
    description: str = ""
    homepage: str = ""
    license: str = ""
    kind: str = "tool"
    """One of: ``tool`` (pip-installed package), ``agent-pack`` (git-clone repo)."""
    python_package: PythonPackage | None = None
    contributes: PluginContributes = field(default_factory=PluginContributes)
    on_install: list[str] = field(default_factory=list)
    on_uninstall: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_path: Path | None = None
    """Path to the manifest file this was loaded from (None if synthesized)."""

    @property
    def is_pip_plugin(self) -> bool:
        return self.python_package is not None

    @property
    def plugin_dir_default(self) -> str:
        """The conventional plugin directory (relative to the repo / package)."""
        return "plugin"


def load_plugin_manifest(path: Path | str) -> PluginManifest:
    p = Path(path)
    if not p.exists():
        raise ManifestError(f"plugin manifest not found: {p}")
    return parse_plugin_manifest(p.read_text(encoding="utf-8"), source=p)


def parse_plugin_manifest(text: str, source: Path | None = None) -> PluginManifest:
    raw = _load_yaml_text(text) or {}
    if not isinstance(raw, dict):
        raise ManifestError(
            f"{_loc(source)}: top-level must be a mapping, got {type(raw).__name__}"
        )
    name = raw.get("name")
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ManifestError(
            f"{_loc(source)}: 'name' must be a string of [a-z0-9_-] starting with a letter"
        )
    version = raw.get("version")
    if not isinstance(version, str) or not version:
        raise ManifestError(f"{_loc(source)}: 'version' must be a non-empty string")
    kind = raw.get("kind", "tool")
    if kind not in ("tool", "agent-pack"):
        raise ManifestError(
            f"{_loc(source)}: 'kind' must be 'tool' or 'agent-pack', got {kind!r}"
        )

    python_package = None
    pp_raw = raw.get("python_package")
    if pp_raw is not None:
        if not isinstance(pp_raw, dict):
            raise ManifestError(f"{_loc(source)}: 'python_package' must be a mapping")
        pp_name = pp_raw.get("name")
        if not isinstance(pp_name, str) or not pp_name:
            raise ManifestError(
                f"{_loc(source)}: 'python_package.name' is required when python_package is set"
            )
        extras = pp_raw.get("extras") or []
        if not isinstance(extras, list):
            raise ManifestError(
                f"{_loc(source)}: 'python_package.extras' must be a list"
            )
        python_package = PythonPackage(
            name=pp_name, extras=[str(e) for e in extras]
        )

    if kind == "tool" and python_package is None:
        # tool-kind plugins are pip-installed; agent-pack plugins are git-clone.
        # We don't hard-fail (kind defaults to tool, but a pure-yaml repo might
        # forget to set kind), but we warn via ManifestError if there's no
        # python_package on a tool. Defer: many tool plugins ARE pip packages,
        # but a tool can be cloned too. So we accept and let install pick the
        # right model based on python_package presence.
        pass

    c_raw = raw.get("contributes") or {}
    if not isinstance(c_raw, dict):
        raise ManifestError(f"{_loc(source)}: 'contributes' must be a mapping")
    contributes = PluginContributes(
        agents=_str_or_none(c_raw.get("agents")),
        skills=_str_or_none(c_raw.get("skills")),
        commands=_str_or_none(c_raw.get("commands")),
        hooks=_str_or_none(c_raw.get("hooks")),
        mcp=_str_or_none(c_raw.get("mcp")),
    )

    on_install = _str_list(raw.get("on_install"), "on_install", source)
    on_uninstall = _str_list(raw.get("on_uninstall"), "on_uninstall", source)
    requires = _str_list(raw.get("requires"), "requires", source)
    tags = _str_list(raw.get("tags"), "tags", source)

    return PluginManifest(
        name=name,
        version=version,
        description=str(raw.get("description") or ""),
        homepage=str(raw.get("homepage") or ""),
        license=str(raw.get("license") or ""),
        kind=kind,
        python_package=python_package,
        contributes=contributes,
        on_install=on_install,
        on_uninstall=on_uninstall,
        requires=requires,
        tags=tags,
        source_path=source,
    )


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ManifestError(f"expected string, got {type(v).__name__}: {v!r}")
    return v


def _str_list(v: Any, field_name: str, source: Path | None) -> list[str]:
    if v is None:
        return []
    if not isinstance(v, list):
        raise ManifestError(f"{_loc(source)}: '{field_name}' must be a list")
    return [str(x) for x in v]


def _loc(source: Path | None) -> str:
    return str(source) if source else "<manifest>"


# ---------------------------------------------------------------------------
# Consumer manifest (.flotilla/manifest.yaml in the project)
# ---------------------------------------------------------------------------


@dataclass
class ConsumerPluginEntry:
    name: str
    version: str = "*"
    """Version spec — pin (``0.16.0``), caret (``^0.16``), or ``*`` (any)."""
    source: str | None = None
    """If present, an alternate source: a git URL or local path. Overrides PyPI for tool plugins."""
    extras: list[str] = field(default_factory=list)


@dataclass
class ConsumerManifest:
    plugins: list[ConsumerPluginEntry] = field(default_factory=list)
    source_path: Path | None = None

    def find(self, name: str) -> ConsumerPluginEntry | None:
        for p in self.plugins:
            if p.name == name:
                return p
        return None


def load_consumer_manifest(path: Path | str) -> ConsumerManifest:
    p = Path(path)
    if not p.exists():
        return ConsumerManifest(source_path=p)
    return parse_consumer_manifest(p.read_text(encoding="utf-8"), source=p)


def parse_consumer_manifest(
    text: str, source: Path | None = None
) -> ConsumerManifest:
    raw = _load_yaml_text(text) or {}
    if not isinstance(raw, dict):
        raise ManifestError(
            f"{_loc(source)}: top-level must be a mapping, got {type(raw).__name__}"
        )
    plugins_raw = raw.get("plugins") or []
    if not isinstance(plugins_raw, list):
        raise ManifestError(f"{_loc(source)}: 'plugins' must be a list")
    plugins: list[ConsumerPluginEntry] = []
    for entry in plugins_raw:
        if not isinstance(entry, dict):
            raise ManifestError(f"{_loc(source)}: each plugin must be a mapping")
        name = entry.get("name")
        if not isinstance(name, str) or not _NAME_RE.match(name):
            raise ManifestError(
                f"{_loc(source)}: plugin 'name' must match [a-z][a-z0-9_-]*"
            )
        version = str(entry.get("version") or "*")
        source_str = _str_or_none(entry.get("source"))
        extras_raw = entry.get("extras") or []
        if not isinstance(extras_raw, list):
            raise ManifestError(
                f"{_loc(source)}: plugin '{name}' extras must be a list"
            )
        plugins.append(
            ConsumerPluginEntry(
                name=name,
                version=version,
                source=source_str,
                extras=[str(e) for e in extras_raw],
            )
        )
    return ConsumerManifest(plugins=plugins, source_path=source)


def write_consumer_manifest(manifest: ConsumerManifest, path: Path) -> None:
    payload = {
        "plugins": [
            _entry_to_dict(p) for p in manifest.plugins
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(payload), encoding="utf-8")


def _entry_to_dict(p: ConsumerPluginEntry) -> dict[str, Any]:
    out: dict[str, Any] = {"name": p.name, "version": p.version}
    if p.source:
        out["source"] = p.source
    if p.extras:
        out["extras"] = list(p.extras)
    return out
