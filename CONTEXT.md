# hupy CONTEXT

*Last updated: 2026-06-30*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — core modules not yet implemented; API may change.

Package: `hupy` · build: `setuptools` · install: `pip install -e ".[dev]"`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed.

| Module | Responsibility |
|---|---|
| `branch_protection` | detect and block annotation markers by severity tier on protected branches |
| `ensure_file_edited` | require specific files or line ranges to be modified in the commit |
| `improve_commit_message` | generate better messages for merge commit types |
| `commit_type` | identify commit type (e.g., binary merge, merge commit) |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

## Annotation Markers

Branch protection operates on *triage tags* grouped into three tiers:

- **Loud** — all-caps (`TODO`, `FIXME`, `HACK`, `BUG`): blocked on protected branches by default
- **Steady** — title-case (`Todo`, `Fixme`, …): configurable
- **Quiet** — lowercase (`todo`, `fixme`, …): configurable

Full taxonomy is defined in the global `CLAUDE.md` under **Triage Tags**.

## Package Layout

```
hupy/                   # installable package
  __init__.py
  branch_protection.py
  ensure_file_edited.py
  improve_commit_message.py
  commit_type.py
tests/
  test_branch_protection.py
  test_ensure_file_edited.py
  test_improve_commit_message.py
  test_commit_type.py
pyproject.toml
```
