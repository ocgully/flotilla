"""Plain-text storage for notes.

Design decision: one line per note, tab-separated ``done<TAB>text``.
See ``.pedia/decisions/0001-plain-text-storage.md`` for the rationale
(ADR: plain text beats SQLite for a ~300 LOC notes CLI).

Storage path resolution (HW-0005):

1. ``$NOTES_PATH`` env var, if set.
2. ``~/.notes.txt`` otherwise.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Note:
    id: int          # 1-based, derived from line position at read time
    done: bool
    text: str

    def render(self) -> str:
        mark = "x" if self.done else " "
        return f"{self.id:>3}. [{mark}] {self.text}"


def store_path() -> Path:
    """Return the on-disk path for the notes file."""
    env = os.environ.get("NOTES_PATH")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".notes.txt"


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic-ish: write to temp then rename.
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    tmp.replace(path)


def load(path: Path | None = None) -> list[Note]:
    path = path or store_path()
    notes: list[Note] = []
    for idx, raw in enumerate(_read_lines(path), start=1):
        if not raw.strip():
            continue
        done_flag, _, text = raw.partition("\t")
        notes.append(Note(id=idx, done=(done_flag == "1"), text=text))
    return notes


def add(text: str, path: Path | None = None) -> Note:
    """Append a new note. Returns the created Note (with its assigned id)."""
    if not text.strip():
        raise ValueError("Note text cannot be empty.")
    path = path or store_path()
    existing = _read_lines(path)
    existing.append(f"0\t{text}")
    _write_lines(path, existing)
    return Note(id=len(existing), done=False, text=text)


def search(query: str, path: Path | None = None) -> list[Note]:
    q = query.lower()
    return [n for n in load(path) if q in n.text.lower()]


def mark_done(note_id: int, path: Path | None = None) -> Note:
    """Flip the ``done`` flag on a note by its 1-based id."""
    path = path or store_path()
    lines = _read_lines(path)
    if not 1 <= note_id <= len(lines):
        raise ValueError(
            f"Note id {note_id} out of range (1..{len(lines)})."
        )
    raw = lines[note_id - 1]
    _, _, text = raw.partition("\t")
    lines[note_id - 1] = f"1\t{text}"
    _write_lines(path, lines)
    return Note(id=note_id, done=True, text=text)
