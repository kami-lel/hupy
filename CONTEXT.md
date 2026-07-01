# hupy CONTEXT

*Last updated: 2026-07-01 — added cli module, refined tt_gating, comprehensive test suite for commit_type*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type` and `kamilog` are implemented; remaining modules are stubs.

Package: `hupy` · build: `setuptools` · install: `pip install -e ".[dev]"` · dependency: `gitpython>=3.1`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | argument parsing, subcommand dispatch, CLI entrypoint |
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression |
| `tt_gating` | **in progress** | gate commits by triage tag presence on protected branches |
| `branch_protection` | not yet implemented | detect and block annotation markers by severity tier on protected branches |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit |
| `improve_commit_message` | not yet implemented | generate better messages for merge commit types |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

## Module Details

### `cli`

Argument parser and entrypoint for the `hupy` command-line tool.

**Public API**: `cli_parser` (ArgumentParser) · `cli_subparser` (subparsers action)

- **main parser** — prog name and description sourced from `__package__` and module docstring
- **subcommand parsers** — registered at module load time; each owns its own argument setup and dispatch function
- **current subcommands** — `triage_tag_gating` / `ttg` (alias): calls `perform_triage_tags_gating(os.getcwd())` with verbosity level applied

Dispatch follows a standard pattern: subcommand dispatch functions receive the parsed `argparse.Namespace` and call the corresponding utility function.

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

Bug fix in 0.1.0: `_is_pull_merge(repo, sha, target_branch)` now returns `False` early if `target_branch` is `None` (detached HEAD) to avoid `TypeError` when accessing `remote.refs[None]`.

### `tt_gating`

Triage tag (TT) gating — blocks commits that introduce annotation markers on protected branches.

**Public API**: `perform_triage_tags_gating(repo_root)` — detect current commit type and block if it introduces TT markers disallowed on the target branch

Module-level logger is shared with `cli` for consistent verbosity control.

Status: **in progress** — core `perform_triage_tags_gating()` stub in place; CLI wiring complete; TT detection and blocking logic not yet implemented.

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
  cli.py                     # argument parsing & dispatch
  commit_type.py             # implemented
  kamilog.py                 # implemented (vendored)
  tt_gating.py               # in progress
tests/
  commit_type_test.py        # comprehensive unit tests w/ pytest fixtures
  testee/
    default_repo.bundle      # minimal git bundle fixture for repo cloning
docs/
  commit_type_hierarchy.md   # CommitType enum diagram
pyproject.toml
```

### Testing Infrastructure

- **pytest fixtures** (`repo_dir`, `repo`) — clone the default bundle and provide repo access; fixtures are scoped per-test and auto-cleaned by `tmp_path`
- **git bundle fixture** (`tests/testee/default_repo.bundle`) — 259-byte single-file repo fixture; tests clone it and dynamically construct scenarios (branches, commits, MERGE_HEAD state)
- **test pattern** — one test class per public function; helper functions for common operations (`_commit`, `_write_merge_head`, `_sha`)
