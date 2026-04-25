# Getting started

A ten-minute tour. Assumes you've done the 6-command quickstart in the
[README](../../README.md).

## 1. See what shipped

```bash
hopewell list
```

You should see the seeded nodes: five closed, two open, one release.

```bash
hopewell show HW-0001
pedia show --for HW-0001
mercator query systems
```

## 2. Add a note (exercise the domain)

```bash
notes add "try the showcase"
notes add "read the tutorial"
notes list
notes search tutorial
notes done 1
notes list
```

The storage lives in `~/.notes.txt` by default; override via `NOTES_PATH=...`.
This is the HW-0005 feature the ledger already records as closed.

## 3. Start a new work item

```bash
hopewell new \
  --components work-item,deliverable,user-facing \
  --title "Export notes to JSON" \
  --priority P2
```

The command prints the new node id (e.g., `HW-0009`). Open the canvas and
you'll see it appear:

```bash
hopewell web --open
```

## 4. Observe a drift block

Edit `.pedia/specs/001-search/spec.md` (change a requirement), then:

```bash
git add .pedia/specs/001-search/spec.md
git commit -m "HW-0003 — tighten search spec"
```

The **pre-commit** hook detects the drift and blocks. Resolve:

```bash
hopewell reconcile --accept
git commit -m "HW-0003 — tighten search spec"   # now passes
```

## 5. Cut a release

```bash
hopewell release start v0.2.0 --scope HW-0006,HW-0007
hopewell release score
# push a release branch — the pre-push hook gates on the score
```

## 6. Query flows

```bash
pedia query "plain text"
pedia trace pedia://decisions/0001-plain-text-storage.md --down

mercator query contract notes
mercator query touches notes/cli.py

hopewell ready
hopewell resume
```

## Next

- [`release-engineering.md`](../release-engineering.md) — how the pre-push
  release-score hook works.
- [`multi-tool.md`](../multi-tool.md) — same loops under Codex and OpenCode.
