---
type: prd
id: PRD-search
title: Search — find a note in under a second
status: shipped
tags: [prd, search]
---

# Search — find a note in under a second

## Goals

- A user with 200 notes can find the one they want in a single shell
  command.
- The command pipeline (type → enter → see match) completes in under 200 ms
  end-to-end on a typical laptop.

## Non-goals

- Ranking matches by relevance.
- Fuzzy matching (typos, transpositions).
- Full-text indexing.

## Success metrics

- `notes search <q>` returns in under 100 ms on a 10k-note file.
- Zero pip-installable dependencies added to support this feature.
- Spec [[spec:001-search]] passes all tests.

## Cited by

- HW-0003 — Search by substring
- HW-0006 — Tagged notes (extends this)

## See also

- [[spec:001-search]] — requirements
- [[decision:0001-plain-text-storage]] — why it's a linear scan
