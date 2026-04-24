"""Tests for the notes CLI. Stdlib ``unittest`` only — no pytest dependency."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from notes import store


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "notes.txt"

    def test_add_and_list(self) -> None:
        store.add("buy milk", path=self.path)
        store.add("call mum", path=self.path)
        loaded = store.load(self.path)
        self.assertEqual([n.text for n in loaded], ["buy milk", "call mum"])
        self.assertEqual([n.id for n in loaded], [1, 2])
        self.assertTrue(all(not n.done for n in loaded))

    def test_empty_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            store.add("   ", path=self.path)

    def test_search_case_insensitive(self) -> None:
        store.add("Buy Milk", path=self.path)
        store.add("write spec", path=self.path)
        self.assertEqual(len(store.search("milk", path=self.path)), 1)
        self.assertEqual(len(store.search("SPEC", path=self.path)), 1)
        self.assertEqual(len(store.search("nope", path=self.path)), 0)

    def test_mark_done(self) -> None:
        store.add("finish showcase", path=self.path)
        n = store.mark_done(1, path=self.path)
        self.assertTrue(n.done)
        self.assertTrue(store.load(self.path)[0].done)

    def test_mark_done_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            store.mark_done(99, path=self.path)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
