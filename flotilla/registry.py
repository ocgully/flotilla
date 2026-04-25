"""Curated plugin registry.

Phase 1 trust model: ``flotilla install <name>`` only succeeds for names
listed in :data:`KNOWN_PLUGINS`. Third-party plugins can still be
installed by passing ``--source <repo-url>`` to ``flotilla install``,
but the bare-name lookup is restricted to keep the install surface
auditable. Phase 2 will add a ``flotilla search`` index and signed
plugin manifests.
"""

from __future__ import annotations

from dataclasses import dataclass


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


KNOWN_PLUGINS: dict[str, KnownPlugin] = {
    "hopewell": KnownPlugin(
        name="hopewell",
        kind="tool",
        pip_package="hopewell",
        repo="https://github.com/ocgully/Hopewell",
        description="Work ledger — typed nodes, flow network, release scoring",
    ),
    "pedia": KnownPlugin(
        name="pedia",
        kind="tool",
        pip_package="pedia",
        repo="https://github.com/ocgully/pedia",
        description="Deterministic knowledge + specs + context for LLM agents",
    ),
    "mercator": KnownPlugin(
        name="mercator",
        kind="tool",
        pip_package="mercator",
        repo="https://github.com/ocgully/mercator",
        description="Layered, AI-friendly codemap CLI for agent consumption",
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
    return KNOWN_PLUGINS.get(name)
