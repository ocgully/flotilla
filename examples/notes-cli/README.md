# notes-cli — a Flotilla-on-a-tiny-domain example

This is the original Flotilla starter kit content, preserved as an
example of how a real project consumes Flotilla plugins. It's a trivial
plain-text notes CLI (~230 LOC) wired up with Hopewell + Pedia + Mercator
+ a slim 6-agent bundle so the *tooling* is the thing you study, not the
business logic.

## What's pre-wired

- `.hopewell/` — work ledger with five historical nodes + two open + one release
- `.pedia/` — knowledge base with one north-star, one constitution chapter, one spec, one decision, one PRD
- `.mercator/` — code map of the notes CLI
- `tests/`, `notes/` — the toy domain itself
- `tutorial/` — the original walkthrough

## Use as a Flotilla example

To re-create this from scratch using the new plugin-marketplace model,
in a fresh project:

```bash
flotilla init
flotilla install hopewell pedia mercator slim-agents
# then re-run the per-tool init scripts from each tool's docs:
hopewell hooks install --full
hopewell network init
pedia init
mercator refresh
```

This directory is preserved so the original tutorial (`tutorial/`) stays
runnable; future Flotilla versions may regenerate it from a recipe.

## See also

- `../../README.md` — top-level Flotilla CLI
- `../../docs/authoring-plugins.md` — author your own plugin
