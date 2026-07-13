# Triage Tag Gating (TTG) Documentation

**Triage Tag Gating** It blocks a merge into a protected branch when the staged changes still contain **triage tags** — the `TODO` / `FIXME` / `HACK` / `BUG` markers that flag unfinished or provisional work — so half-done code doesn't slip into `dev` or `main`.

### Triage Tags

Each marker comes in three tiers, distinguished by letter case:

| Tier | Case | Markers |
|---|---|---|
| **Loud** | all-caps | `TODO` `FIXME` `HACK` `BUG` |
| **Steady** | capitalized | `Todo` `Fixme` `Hack` `Bug` |
| **Quiet** | lowercase | `todo` `fixme` `hack` `bug` |

The tier signals how much the marker matters — Loud demands attention, Quiet is a low-priority note.

### What It Gates

TTG only acts on the two protected merges, and the release gate is stricter:

| Merge | Blocks |
|---|---|
| **Feature Landing** — a feature branch merged into `dev` | Loud |
| **Version Release** — `dev` merged into `main` | Loud + Steady |
| anything else (regular commit, unrelated merge) | *nothing* |

Quiet tags are never blocked, so low-priority notes can travel with the code.

TTG runs in the pre-commit stage, right after [Ban Direct Commit](bdc_doc.md) — see the [Hook Chain](hook_chain_doc.md) for where it fits. **Feature Landing** and **Version Release** are merge types defined in [Commit, Branch & Merge](cbm_doc.md).
