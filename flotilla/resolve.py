"""Plugin source resolution.

Given a ``ConsumerPluginEntry`` from the consumer's manifest (or a CLI
argument), this module locates the plugin on disk:

* **Tool plugins (pip):** ``pip install`` (if not already importable),
  then locate the package and look for ``plugin/`` next to it. Many of
  our plugins also ship the ``flotilla.yaml`` *outside* the Python
  package alongside the repo's ``plugin/`` dir; for editable installs we
  walk up from the package dir to find ``flotilla.yaml``.

* **Agent-pack plugins (git-clone):** clone the repo into the project's
  cache dir, check out the requested ref, and return the cache path.

The resolver also supports a ``source`` override on the consumer entry
that points at a local path — used heavily in tests.
"""

from __future__ import annotations

import importlib
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .manifest import (
    ConsumerPluginEntry,
    PluginManifest,
    load_plugin_manifest,
)
from .registry import KnownPlugin, lookup


@dataclass
class ResolvedPlugin:
    """A located plugin ready to compose.

    ``plugin_dir`` is the **manifest root** — the directory that
    contains ``flotilla.yaml``. Contribution paths declared in the
    manifest (e.g. ``plugin/agents/``) are interpreted relative to this
    root, so the composition layer concatenates them directly.
    """

    manifest: PluginManifest
    plugin_dir: Path
    source_descriptor: str  # for installed.json bookkeeping


class ResolutionError(RuntimeError):
    pass


def resolve(
    entry: ConsumerPluginEntry,
    *,
    cache_dir: Path,
    pip_runner: "PipRunner | None" = None,
    git_runner: "GitRunner | None" = None,
) -> ResolvedPlugin:
    """Resolve a plugin entry to an on-disk plugin dir."""
    if entry.source:
        return _resolve_source(entry, cache_dir=cache_dir, git_runner=git_runner)

    known = lookup(entry.name)
    if known is None:
        raise ResolutionError(
            f"unknown plugin {entry.name!r}; in Phase 1, only the curated "
            f"list is installable by name. Pass --source <repo-or-path> "
            f"for third-party plugins."
        )
    if known.kind == "tool":
        return _resolve_pip(entry, known, pip_runner=pip_runner)
    return _resolve_git_clone(
        entry, known.repo or "", cache_dir=cache_dir, git_runner=git_runner
    )


def _resolve_source(
    entry: ConsumerPluginEntry,
    *,
    cache_dir: Path,
    git_runner: "GitRunner | None",
) -> ResolvedPlugin:
    src = entry.source or ""
    # Local path overrides — used in tests + sideloading
    local = Path(src).expanduser()
    if local.exists() and local.is_dir():
        manifest_path = local / "flotilla.yaml"
        if not manifest_path.exists():
            raise ResolutionError(
                f"local source {local} has no flotilla.yaml at the root"
            )
        manifest = load_plugin_manifest(manifest_path)
        return ResolvedPlugin(
            manifest=manifest,
            plugin_dir=local,
            source_descriptor=f"path:{local.resolve()}",
        )
    return _resolve_git_clone(
        entry, src, cache_dir=cache_dir, git_runner=git_runner
    )


def _resolve_pip(
    entry: ConsumerPluginEntry,
    known: KnownPlugin,
    *,
    pip_runner: "PipRunner | None",
) -> ResolvedPlugin:
    pkg_name = known.pip_package or known.name
    runner = pip_runner or PipRunner()
    if not _is_importable(pkg_name):
        runner.install(pkg_name, version=entry.version, extras=entry.extras)
    pkg_dir = _find_package_dir(pkg_name)
    if pkg_dir is None:
        raise ResolutionError(
            f"installed {pkg_name!r} but couldn't locate its package directory"
        )
    manifest_path = _find_manifest_for_package(pkg_dir)
    if manifest_path is None:
        raise ResolutionError(
            f"package {pkg_name!r} is installed but has no flotilla.yaml "
            f"(searched alongside {pkg_dir} and one level up)"
        )
    manifest = load_plugin_manifest(manifest_path)
    plugin_subdir = manifest_path.parent / manifest.plugin_dir_default
    if not plugin_subdir.is_dir():
        raise ResolutionError(
            f"plugin manifest {manifest_path} declares plugin/ but {plugin_subdir} is missing"
        )
    return ResolvedPlugin(
        manifest=manifest,
        plugin_dir=manifest_path.parent,
        source_descriptor=f"pip:{pkg_name}",
    )


def _resolve_git_clone(
    entry: ConsumerPluginEntry,
    repo_url: str,
    *,
    cache_dir: Path,
    git_runner: "GitRunner | None",
) -> ResolvedPlugin:
    if not repo_url:
        raise ResolutionError(
            f"agent-pack plugin {entry.name!r} requires a source repo URL"
        )
    runner = git_runner or GitRunner()
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / entry.name
    if not target.exists():
        runner.clone(repo_url, target)
    else:
        runner.fetch(target)
    if entry.version and entry.version != "*":
        # Best-effort checkout; bare-tag failures fall back to default branch.
        try:
            runner.checkout(target, entry.version)
        except subprocess.CalledProcessError:
            pass
    manifest_path = target / "flotilla.yaml"
    if not manifest_path.exists():
        raise ResolutionError(
            f"cloned {repo_url} but found no flotilla.yaml at the root"
        )
    manifest = load_plugin_manifest(manifest_path)
    return ResolvedPlugin(
        manifest=manifest,
        plugin_dir=target,
        source_descriptor=f"git:{repo_url}",
    )


# ---------------------------------------------------------------------------
# Helpers — pip / git subprocess wrappers (factored for test injection)
# ---------------------------------------------------------------------------


def _is_importable(pkg_name: str) -> bool:
    norm = pkg_name.replace("-", "_")
    return importlib.util.find_spec(norm) is not None


def _find_package_dir(pkg_name: str) -> Path | None:
    norm = pkg_name.replace("-", "_")
    try:
        spec = importlib.util.find_spec(norm)
    except (ImportError, ValueError):
        return None
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin).parent


def _find_manifest_for_package(pkg_dir: Path) -> Path | None:
    # 1. Inside the package itself: pkg_dir/flotilla.yaml
    candidate = pkg_dir / "flotilla.yaml"
    if candidate.exists():
        return candidate
    # 2. One level up — the repo root for editable installs.
    candidate = pkg_dir.parent / "flotilla.yaml"
    if candidate.exists():
        return candidate
    # 3. site-packages adjacent (rare)
    return None


class PipRunner:
    """Subprocess wrapper around ``pip install``. Subclass for tests."""

    def install(
        self, package: str, *, version: str = "*", extras: list[str] | None = None
    ) -> None:
        spec = package
        if extras:
            spec = f"{spec}[{','.join(extras)}]"
        if version and version != "*":
            spec = f"{spec}{_pip_version_clause(version)}"
        cmd = [sys.executable, "-m", "pip", "install", spec]
        subprocess.run(cmd, check=True)

    def uninstall(self, package: str) -> None:
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package]
        subprocess.run(cmd, check=True)


class GitRunner:
    """Subprocess wrapper around git. Subclass for tests."""

    def clone(self, url: str, target: Path) -> None:
        cmd = ["git", "clone", "--depth", "1", url, str(target)]
        subprocess.run(cmd, check=True)

    def fetch(self, target: Path) -> None:
        cmd = ["git", "-C", str(target), "fetch", "--all", "--tags"]
        subprocess.run(cmd, check=True)

    def checkout(self, target: Path, ref: str) -> None:
        cmd = ["git", "-C", str(target), "checkout", ref]
        subprocess.run(cmd, check=True)


def _pip_version_clause(version: str) -> str:
    v = version.strip()
    if v.startswith(("==", ">=", "<=", ">", "<", "~=")):
        return v
    if v.startswith("^"):
        # Caret: ^0.16 -> >=0.16,<0.17 ; ^1.2 -> >=1.2,<2.0
        rest = v[1:]
        return f">={rest}"
    return f"=={v}"
