# Triage Tag Gating (TTG) Documentation

**Triage Tag Gating** is *HUPy*'s `pre-commit` hook. It blocks a merge into a protected branch when the staged changes still contain **triage tags** — the `TODO` / `FIXME` / `HACK` / `BUG` markers that flag unfinished or provisional work — so half-done code doesn't slip into `dev` or `main`.

## Triage Tags

Each marker comes in three tiers, distinguished by letter case:

| Tier | Case | Markers |
|---|---|---|
| **Loud** | all-caps | `TODO` `FIXME` `HACK` `BUG` |
| **Steady** | capitalized | `Todo` `Fixme` `Hack` `Bug` |
| **Quiet** | lowercase | `todo` `fixme` `hack` `bug` |

The tier signals how much the marker matters — Loud demands attention, Quiet is a low-priority note.

## What It Gates

TTG only acts on the two protected merges, and the release gate is stricter:

| Merge | Blocks |
|---|---|
| **Feature Landing** — a feature branch merged into `dev` | Loud |
| **Stable Release** — `dev` merged into `main` | Loud + Steady |
| anything else (regular commit, unrelated merge) | *nothing* |

Quiet tags are never blocked, so low-priority notes can travel with the code.

## When It Blocks

If a gated marker is found in the staged changes, the commit is **stopped** and *HUPy* prints each offending file and line so you can see exactly what to resolve. To get past the gate, either finish and remove the marker, or **lower its tier** — e.g. change a `TODO` to a `todo` — to signal it's an accepted, low-priority note.

Every other commit passes straight through untouched.
