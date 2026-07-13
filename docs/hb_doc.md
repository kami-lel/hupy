# Hook Bracket (HB) Documentation

**Hook Bracket (HB)** lets you run your own shell commands alongside *HUPy*'s git hooks, without writing a custom hook yourself.

## Lead And Trail

For each hook — `pre-commit`, `prepare-commit-msg`, and `post-commit` — you configure two lists of commands:

- **lead** commands run *before* HUPy's own checks
- **trail** commands run *after* HUPy's own checks

Slot in linting, formatting, notifications, or anything else your workflow needs, right around the checks HUPy already runs.

See the [Hook Chain](hook_chain_doc.md) for where each *lead*/*trail* pair sits relative to [Ban Direct Commit](bdc_doc.md), [Triage Tag Gating](ttg_doc.md), and [Prepend Commit Header](pch_doc.md). An HB entry's `allow_commit_types` filters on the commit and merge types defined in [Commit, Branch & Merge](cbm_doc.md).
