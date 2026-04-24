---
type: constitution
chapter: technical
title: Technical constitution
universal_context: true
tags: [constitution, technical]
---

# Technical constitution

## Stdlib only

The `notes` package may depend on the Python standard library, nothing
else. No runtime `requirements.txt`. If you find yourself reaching for a
third-party package, reconsider — the domain is too small for it.

Exception: development dependencies (test runners, linters) may be listed
in `pyproject.toml` under optional-dependencies. The shipped application
stays stdlib.

## Plain text wins

Storage is a single plain-text file. One line per note. `done<TAB>text`.
See [[decision:0001-plain-text-storage]] for the rationale.

## Startup under 100 ms

No imports that cost more than a few milliseconds each. Benchmark target:
`time notes list` on an empty store completes in under 100 ms cold.

## ~300 LOC budget

The `notes/` package should stay under 300 lines of code. When you hit the
budget, the answer is "remove something," not "raise the budget."

## Tests are stdlib unittest

No pytest dependency. `python -m unittest discover` is the blessed
invocation.
