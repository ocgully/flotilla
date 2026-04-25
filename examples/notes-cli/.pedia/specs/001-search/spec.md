---
type: spec
id: spec-001-search
title: Search notes by substring
status: shipped
defines: [Search]
tags: [spec, search]
---

# Search notes by substring

## Context

Users who accumulate more than ~20 notes need a way to find one quickly.
`notes list` alone doesn't scale.

## Requirements

1. **Substring match.** A query matches a note if the query string (lowered)
   appears anywhere in the note text (lowered).
2. **Case-insensitive.** `milk`, `Milk`, and `MILK` all match "Buy Milk."
3. **No regex.** The domain is small; plain substring is enough and keeps
   the contract obvious.
4. **Exit code 0 on no-match.** Print a friendly "no matches" message and
   return 0. Only argparse errors return non-zero.

## Non-requirements

- Fuzzy matching
- Ranking
- Indexing (a linear scan of `~/.notes.txt` is fine for < 10k notes)

## Cited by

- HW-0003 — Search by substring (closed)
- HW-0006 — Tagged notes (open) — extends search

## See also

- [[decision:0001-plain-text-storage]] — why search is a linear scan
- [[prd:search]] — product framing
