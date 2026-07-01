# hupy CONTEXT

*Last updated: 2026-07-01*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type` and `kamilog` are implemented; remaining modules are stubs.

Package: `hupy` · build: `setuptools` · install: `pip install -e ".[dev]"` · dependency: `gitpython>=3.1`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed.

| Module | Status | Responsibility |
|---|---|---|
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression |
| `branch_protection` | not yet implemented | detect and block annotation markers by severity tier on protected branches |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit |
| `improve_commit_message` | not yet implemented | generate better messages for merge commit types |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

## Module Details

### `commit_type`

Identifies the type of an in-progress git commit by inspecting git state files.

**Public API**: `get_current_commit_type(repo_path=".")` → `CommitType`

**`CommitType(Flag)`** — two-level bitmask hierarchy:

- level 1: `MERGE` | `OTHER_COMMIT`
- level 2 (under `MERGE`): `FEATURE_FINISH` | `VERSION_RELEASE` | `OTHER_MERGE`

Classification logic (in order):

1. no `MERGE_HEAD` → `OTHER_COMMIT`
2. `MERGE_HEAD` has multiple lines (octopus merge) → `OTHER_MERGE`
3. `MERGE_HEAD` SHA matches any remote tracking ref of the current branch (pull merge) → `OTHER_MERGE`
4. source branch ≠ `MAIN_BRANCH` and target == `DEV_BRANCH` → `FEATURE_FINISH`
5. source == `DEV_BRANCH` and target == `MAIN_BRANCH` → `VERSION_RELEASE`
6. all other merges → `OTHER_MERGE`

Module-level constants `MAIN_BRANCH = "main"` and `DEV_BRANCH = "develop"` control branch name matching. `CHERRY_PICK_HEAD` and `REVERT_HEAD` detection is present in git but the corresponding `CommitType` members are not yet defined.

Reference diagram: `docs/commit_type_hierarchy.md`

### `kamilog`

Customized logging module vendored from [github.com/kami-lel/kamilog](https://github.com/kami-lel/kamilog) (v1.7.0).

Key entities:

- **`KamiLogger`** — `logging.Logger` subclass; adds `.enter()`, `.skip()`, `.succ()`, `.pass_()`, `.done()`, `.fail()` methods for six extra levels between standard ones
- **`AnsiColor` / `AnsiRenderer`** — TTY-aware 16-color ANSI support; coloring is a no-op when the stream is not a TTY
- **`_LogFormatEngine` / `_LogFormatter`** — builds `LEVEL source: message` lines with optional absolute or relative timestamps
- **`_DiffOnlyEngine`** — sliding-window diff compression; replaces repeated character runs with `〃\t` markers aligned to 8-column tab stops
- **`getLogger(name, *, datefmt, relative_to)`** — public factory; returns a `KamiLogger` with stdout handler (< WARNING) and stderr handler (≥ WARNING) pre-attached
- **`add_verbose_arguments(parser)` / `set_logging_level_by_verbosity(namespace)`** — argparse `-v`/`-q` verbosity helpers
- **`print_line_padding_centered/left_just/right_just`** — decorative separator lines with a fill character

Custom log levels (numeric order):

| level | value | meaning |
|---|---|---|
| `ENTER` | 11 | entering a hook or test case |
| `SKIP` | 12 | skipping a hook or test case |
| `SUCC` | 15 | task or operation succeeded |
| `PASS` | 21 | hook or test case passed |
| `DONE` | 25 | task or operation completed |
| `FAIL` | 45 | hook or test case failed |

## Annotation Markers

Branch protection operates on *triage tags* grouped into three tiers:

- **Loud** — all-caps (`TODO`, `FIXME`, `HACK`, `BUG`): blocked on protected branches by default
- **Steady** — title-case (`Todo`, `Fixme`, …): configurable
- **Quiet** — lowercase (`todo`, `fixme`, …): configurable

Full taxonomy is defined in the global `CLAUDE.md` under **Triage Tags**.

## Package Layout

```
hupy/                        # installable package
  __init__.py
  commit_type.py             # implemented
  kamilog.py                 # implemented
docs/
  commit_type_hierarchy.md   # CommitType enum diagram
pyproject.toml
```
