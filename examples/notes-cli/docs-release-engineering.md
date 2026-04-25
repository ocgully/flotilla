# Release engineering

This project ships with the full Hopewell git-hook stack
(`hopewell hooks install --full`). That means:

## The hook chain

| Hook | Purpose | What blocks |
|------|---------|-------------|
| `pre-commit` | Drift detection; Mercator boundary check | Spec drift without a reconcile; boundary violations at error severity |
| `commit-msg` | Require an `HW-NNNN` reference in non-merge, non-fixup commits | Missing HW-ref |
| `post-commit` | Hopewell event (auto-touch / auto-close on `fixes HW-NNNN`); Mercator + Pedia incremental refresh | — (advisory) |
| `pre-push` | On a `release/*` branch, compute the release confidence score; block if below threshold | Score below threshold |

## Cutting a release

```bash
# 1. Declare the release and scope
hopewell release start v0.2.0 --scope HW-0006,HW-0007

# 2. Get the current confidence score
hopewell release score

# 3. (Optional) Generate a report
hopewell release report

# 4. Finalise
hopewell release finalize
```

## Auto-enforced routes

The flow network (see `hopewell network show`) distinguishes between routes
that require orchestrator judgment and routes that are automated. The
following routes in this project are marked `auto_enforced: true`:

- `code-review -> github-main [on_pass]` — handled by the pre-push
  release-score gate.
- `code-review -> @architect [on_fail]` — handled by commit-msg rejection.
- `ci-pipeline -> uat-gate [on_pass]` — handled by the post-commit event
  flow.
- `ci-pipeline -> @architect [on_fail]` — handled by the post-commit
  rework signal.

When you open `hopewell web`, these routes render as **dashed grey** edges
to signal "no orchestrator judgment needed here — the hook has it."

## Release-score inputs

The score is computed from:

- **Attestations** on in-scope nodes (pass/fail/waived)
- **UAT status** on in-scope nodes (if `needs-uat` component present)
- **Release scope coherence** (all referenced nodes exist + reachable)

See `hopewell release score --format json` for the breakdown.
