"""Curated plugin registry.

Phase 1 trust model: ``flotilla install <name>`` only succeeds for names
listed in :data:`KNOWN_PLUGINS`. Third-party plugins can still be
installed by passing ``--source <repo-url>`` to ``flotilla install``,
but the bare-name lookup is restricted to keep the install surface
auditable. Phase 2 will add a ``flotilla search`` index and signed
plugin manifests.

Aliases (legacy names from rebrands) are resolved transparently by
:func:`lookup` so existing ``flotilla install <legacy>`` invocations
continue to work after a plugin renames.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnownPlugin:
    name: str
    kind: str
    """``tool`` (pip) or ``agent-pack`` (git-clone)."""
    pip_package: str | None = None
    """For ``tool`` plugins, the name to ``pip install``."""
    repo: str | None = None
    """For ``agent-pack`` plugins (and as a homepage hint), the git repo URL."""
    description: str = ""
    aliases: tuple[str, ...] = ()
    """Legacy names this plugin also answers to (rebrand support)."""


KNOWN_PLUGINS: dict[str, KnownPlugin] = {
    "taskflow": KnownPlugin(
        name="taskflow",
        kind="tool",
        pip_package="taskflow",
        repo="https://github.com/ocgully/Hopewell",
        description="Work ledger — typed nodes, flow network, release scoring (formerly hopewell)",
        aliases=("hopewell",),
    ),
    "pedia": KnownPlugin(
        name="pedia",
        kind="tool",
        pip_package="pedia",
        repo="https://github.com/ocgully/pedia",
        description="Deterministic knowledge + specs + context for LLM agents",
    ),
    "codeatlas": KnownPlugin(
        name="codeatlas",
        kind="tool",
        pip_package="codeatlas",
        repo="https://github.com/ocgully/mercator",
        description="Layered, AI-friendly codemap CLI for agent consumption (formerly mercator/codemap)",
        aliases=("mercator", "codemap"),
    ),
    "diffsextant": KnownPlugin(
        name="diffsextant",
        kind="tool",
        pip_package="diffsextant",
        repo="https://github.com/ocgully/sextant",
        description="Semantic-operation diff classifier (formerly sextant)",
        aliases=("sextant",),
    ),
    "slim-agents": KnownPlugin(
        name="slim-agents",
        kind="agent-pack",
        pip_package=None,
        repo="https://github.com/ocgully/flotilla-slim-agents",
        description="Bare-bones 6-role AIDLC agent bundle",
    ),
}


def lookup(name: str) -> KnownPlugin | None:
    """Look up a plugin by its primary name OR any legacy alias."""
    direct = KNOWN_PLUGINS.get(name)
    if direct is not None:
        return direct
    for plugin in KNOWN_PLUGINS.values():
        if name in plugin.aliases:
            return plugin
    return None
