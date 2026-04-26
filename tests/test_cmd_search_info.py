"""``flotilla search`` and ``flotilla info`` Phase-2 stub tests."""

from __future__ import annotations

import argparse

from flotilla.commands import cmd_info, cmd_search


def test_search_stub_message(capsys):
    rc = cmd_search(argparse.Namespace(query=""))
    assert rc == 0
    out = capsys.readouterr().out
    assert "deferred to Phase 2" in out
    assert "taskflow" in out and "pedia" in out and "codeatlas" in out
    # Legacy aliases still surface so users hitting old docs find the path.
    assert "hopewell" in out and "mercator" in out


def test_info_known_plugin(capsys):
    # `info` resolves legacy aliases through the registry, so calling
    # with the old name still surfaces the (renamed) canonical plugin.
    rc = cmd_info(argparse.Namespace(name="hopewell"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "taskflow" in out or "hopewell" in out
    assert "tool" in out


def test_info_unknown_plugin(capsys):
    rc = cmd_info(argparse.Namespace(name="not-a-real-plugin"))
    assert rc == 1
    assert "curated registry" in capsys.readouterr().out
