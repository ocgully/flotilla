"""End-to-end test: install Hopewell as a pip plugin.

This test uses ``--source <local-path>`` to point Flotilla at the local
Hopewell checkout (so it does not need network access or a published
registry), but it exercises the full pip-plugin code path:

1. Resolve the manifest at ``C:/git/hopewell/flotilla.yaml``
2. Compose contributions into ``.claude/`` (agents, commands, hooks)
3. Run ``hopewell hooks install`` via the on_install step (skipped here
   to keep the test hermetic — the hooks-install step writes outside
   the tmp project)
4. Verify the contributed files landed
5. Verify settings.json was merged correctly under the sentinel
6. ``flotilla remove hopewell`` and verify cleanup

The test is skipped if ``C:/git/hopewell/flotilla.yaml`` is not present
(developer running outside the AgentFactory monorepo).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pytest

from flotilla.commands import cmd_init, cmd_install, cmd_list, cmd_remove


HOPEWELL_REPO = Path(os.environ.get("HOPEWELL_REPO", r"C:/git/hopewell"))


@pytest.mark.skipif(
    not (HOPEWELL_REPO / "flotilla.yaml").exists(),
    reason="hopewell checkout not present — set HOPEWELL_REPO env var to override",
)
def test_install_hopewell_end_to_end(tmp_project: Path):
    cmd_init(argparse.Namespace(path=str(tmp_project), force=False))

    # --no-run-install so we don't try to install hopewell git hooks into
    # the tmp project (that would call out to real git in a non-repo).
    rc = cmd_install(
        argparse.Namespace(
            names=["hopewell"],
            source=str(HOPEWELL_REPO),
            version="*",
            extras="",
            no_run_install=True,
        )
    )
    assert rc == 0

    # Agents contributed
    scribe = tmp_project / ".claude" / "agents" / "hopewell-scribe.md"
    assert scribe.exists(), f"missing {scribe}"
    assert "Hopewell Scribe" in scribe.read_text(encoding="utf-8")

    # Commands contributed
    hw_cmd = tmp_project / ".claude" / "commands" / "hw.md"
    assert hw_cmd.exists()

    # Hooks merged. After the rebrand the manifest's canonical name is
    # `taskflow`; installing via the legacy alias `hopewell` records under
    # the new canonical key. Either name in the managed map satisfies us.
    settings_path = tmp_project / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "flotilla:managed" in settings
    managed = settings["flotilla:managed"]
    assert ("taskflow" in managed) or ("hopewell" in managed)
    assert "hooks" in settings
    assert "SessionStart" in settings["hooks"]

    # installed.json records the install (under the canonical name post-rebrand).
    db = json.loads(
        (tmp_project / ".flotilla" / "installed.json").read_text(encoding="utf-8")
    )
    plugin_key = "taskflow" if "taskflow" in db["plugins"] else "hopewell"
    assert plugin_key in db["plugins"]
    assert db["plugins"][plugin_key]["kind"] == "tool"

    # `flotilla list` shows it
    rc = cmd_list(argparse.Namespace(format="json"))
    assert rc == 0


@pytest.mark.skipif(
    not (HOPEWELL_REPO / "flotilla.yaml").exists(),
    reason="hopewell checkout not present",
)
def test_remove_hopewell_cleans_up(tmp_project: Path):
    cmd_init(argparse.Namespace(path=str(tmp_project), force=False))
    cmd_install(
        argparse.Namespace(
            names=["hopewell"],
            source=str(HOPEWELL_REPO),
            version="*",
            extras="",
            no_run_install=True,
        )
    )
    rc = cmd_remove(
        argparse.Namespace(
            name="hopewell", keep_pip=True, no_run_uninstall=True
        )
    )
    assert rc == 0
    assert not (tmp_project / ".claude" / "agents" / "hopewell-scribe.md").exists()
    settings = json.loads(
        (tmp_project / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    managed = settings.get("flotilla:managed", {})
    # After remove neither the legacy nor the new canonical key remains.
    assert "hopewell" not in managed
    assert "taskflow" not in managed
    db = json.loads(
        (tmp_project / ".flotilla" / "installed.json").read_text(encoding="utf-8")
    )
    assert "hopewell" not in db["plugins"]
