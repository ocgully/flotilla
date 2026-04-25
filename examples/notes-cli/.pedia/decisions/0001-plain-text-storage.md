---
type: decision
id: ADR-0001
title: Plain-text storage (not SQLite)
status: accepted
date: 2026-04-20
tags: [decision, storage]
---

# ADR-0001: Plain-text storage (not SQLite)

## Context

The notes CLI needs persistent storage. Obvious options:

1. **Plain text** — one line per note, `done<TAB>text`.
2. **SQLite** — Python stdlib, proper ids, transactional.
3. **JSON array** — one file, stdlib, structured.

## Decision

**Plain text, one line per note.**

## Consequences

**Good:**

- Human-editable. Open `~/.notes.txt` in any editor.
- Trivial to back up (copy the file).
- No migration surface when we add fields — just add a column and handle
  absence.
- Startup cost is a single file read. No connection, no schema check.
- Aligns with the [[constitution:technical]] "plain text wins" rule.

**Bad:**

- Linear scan on every operation. Fine up to ~10k notes; unacceptable at
  1M. We are very comfortable with that limit for this product.
- No atomic transactions. Mitigated by writing to `notes.txt.tmp` then
  rename — good enough for the single-user, single-process case.
- IDs are positional (1-based line number). Deleting lines shifts ids.
  Acceptable because we don't delete — `notes done` only flips a flag.

## See also

- [[north-star:01-small-fast-notes]]
- [[spec:001-search]]
