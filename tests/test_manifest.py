"""Manifest parser + validator tests.

Covers both manifest shapes (plugin-side ``flotilla.yaml`` and
consumer-side ``.flotilla/manifest.yaml``) and the friendly error
messages the validator surfaces.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flotilla.manifest import (
    ConsumerPluginEntry,
    ManifestError,
    load_consumer_manifest,
    load_plugin_manifest,
    parse_consumer_manifest,
    parse_plugin_manifest,
    write_consumer_manifest,
    ConsumerManifest,
)


def test_plugin_manifest_minimal():
    text = "name: hopewell\nversion: 0.1.0\n"
    m = parse_plugin_manifest(text)
    assert m.name == "hopewell"
    assert m.version == "0.1.0"
    assert m.kind == "tool"
    assert m.python_package is None
    assert not m.contributes.agents


def test_plugin_manifest_full():
    text = (
        "name: hopewell\n"
        "version: 0.16.0\n"
        "description: Work ledger\n"
        "kind: tool\n"
        "python_package:\n"
        "  name: hopewell\n"
        "  extras:\n"
        "    - web\n"
        "    - github\n"
        "contributes:\n"
        "  agents: plugin/agents/\n"
        "  hooks: plugin/hooks.yaml\n"
        "on_install:\n"
        "  - hopewell hooks install --full --quiet\n"
        "  - hopewell network init --quiet\n"
        "tags:\n"
        "  - ledger\n"
    )
    m = parse_plugin_manifest(text)
    assert m.python_package is not None
    assert m.python_package.name == "hopewell"
    assert m.python_package.extras == ["web", "github"]
    assert m.contributes.agents == "plugin/agents/"
    assert m.contributes.hooks == "plugin/hooks.yaml"
    assert m.on_install == [
        "hopewell hooks install --full --quiet",
        "hopewell network init --quiet",
    ]
    assert m.is_pip_plugin
    assert m.tags == ["ledger"]


def test_plugin_manifest_aliases():
    """The `aliases:` list lets a renamed plugin keep answering to its
    legacy names so consumers' existing manifests don't break."""
    text = (
        "name: taskflow\n"
        "version: 0.17.0\n"
        "kind: tool\n"
        "aliases:\n"
        "  - hopewell\n"
        "python_package:\n"
        "  name: taskflow\n"
    )
    m = parse_plugin_manifest(text)
    assert m.aliases == ["hopewell"]
    # Default when omitted is an empty list.
    text_no_aliases = (
        "name: pedia\n"
        "version: 0.3.0\n"
        "kind: tool\n"
        "python_package:\n"
        "  name: pedia\n"
    )
    m2 = parse_plugin_manifest(text_no_aliases)
    assert m2.aliases == []


def test_registry_lookup_resolves_aliases():
    """`flotilla install hopewell` must continue to resolve to the new
    `taskflow` plugin during the deprecation window."""
    from flotilla.registry import lookup
    direct = lookup("taskflow")
    via_alias = lookup("hopewell")
    assert direct is not None
    assert via_alias is direct  # same KnownPlugin object
    # Same for the codeatlas / mercator pair
    assert lookup("mercator") is lookup("codeatlas")
    # And diffsextant / sextant
    assert lookup("sextant") is lookup("diffsextant")
    # Unknown name still returns None
    assert lookup("totally-not-real") is None


def test_plugin_manifest_rejects_bad_name():
    with pytest.raises(ManifestError):
        parse_plugin_manifest("name: 9bad\nversion: 0.1.0\n")
    with pytest.raises(ManifestError):
        parse_plugin_manifest("name: Bad-Caps\nversion: 0.1.0\n")


def test_plugin_manifest_rejects_bad_kind():
    with pytest.raises(ManifestError, match="kind"):
        parse_plugin_manifest("name: x\nversion: 0.1.0\nkind: weird\n")


def test_plugin_manifest_rejects_missing_version():
    with pytest.raises(ManifestError, match="version"):
        parse_plugin_manifest("name: x\n")


def test_load_plugin_manifest_missing_file(tmp_path: Path):
    with pytest.raises(ManifestError, match="not found"):
        load_plugin_manifest(tmp_path / "absent.yaml")


def test_consumer_manifest_roundtrip(tmp_path: Path):
    cm = ConsumerManifest(
        plugins=[
            ConsumerPluginEntry(name="hopewell", version="^0.16.0", extras=["web"]),
            ConsumerPluginEntry(name="pedia", version="*"),
        ]
    )
    p = tmp_path / "manifest.yaml"
    write_consumer_manifest(cm, p)
    loaded = load_consumer_manifest(p)
    assert [pl.name for pl in loaded.plugins] == ["hopewell", "pedia"]
    assert loaded.find("hopewell").extras == ["web"]
    assert loaded.find("pedia").version == "*"


def test_consumer_manifest_rejects_bad_plugin():
    with pytest.raises(ManifestError):
        parse_consumer_manifest("plugins:\n  - name: 9bad\n")
