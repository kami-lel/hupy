# hupy CONTEXT

*Last updated: 2026-07-02 — added PCH (Prepend Commit Header) module and comprehensive test suite; refactored CLI parsers into separate modules; fixed branch-name mismatch in commit_type_test.py*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type`, `kamilog`, `cli`, and the `ttg` package (Triage Tag Gating) are implemented; `branch_protection`, `ensure_file_edited`, and `improve_commit_message` are not yet started.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependency: `gitpython>=3.1`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | argument parsing, subcommand dispatch, CLI entrypoint |
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for Feature Finish and Version Release merges |
| `ttg.tt_detect` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.tt_gating` | **implemented** | gate commits by triage tag presence on protected branches |
| `branch_protection` | not yet implemented | detect and block annotation markers by severity tier on protected branches |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

## Module Details

### `commit_type`

Identifies the type of an in-progress git commit by inspecting git state files.

**Public API**: `get_current_commit_type(repo_path)` → `CommitType`

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

Module-level constants `MAIN_BRANCH = "main"` and `DEV_BRANCH = "dev"` control branch name matching. `CHERRY_PICK_HEAD` and `REVERT_HEAD` detection is present in git but the corresponding `CommitType` members are not yet defined.

`_is_pull_merge(repo, sha, target_branch)` returns `False` early if `target_branch` is `None` (detached HEAD) to avoid `TypeError` when accessing `remote.refs[None]`.

### `pch`

Prepend Commit Header — rewrites in-progress commit messages to prepend informational headers for merge commits.

**Public API**: `prepend_commit_header(repo_root)` — detect current commit type via the top-level `commit_type` module, then prepend an appropriate header and rewrite `.git/COMMIT_EDITMSG`

Header generation logic:

- `FEATURE_FINISH` merge → `"Feature Finish: <source-branch-name>"` + blank line + original message
- `VERSION_RELEASE` merge → `"Version Release"` + blank line + original message
- all other commit types → file left untouched, no exception

The rewrite separates comment lines (starting with `#`) from content, placing all comments after the content block to preserve git's template comments. Non-destructive on failure: if the atomic write via `os.replace()` fails, the original file is untouched and the temporary file is cleaned up.

### `ttg.tt_detect`

Scans staged git diffs for triage tag annotation markers.

**Public API**: `detect_triage_tags_in_staged_file(file_path, repo_root=None)` → `list[(TriageTagType, str)]` — runs `git diff --cached -- file_path`, and for every added (`+`) line, records the first matching tag and the line text

**`TriageTagType(Flag)`** — 12 members across 3 tiers × 4 kinds (`TODO`/`FIXME`/`HACK`/`BUG`), each matched case-sensitively (`TODO` loud, `Todo` steady, `todo` quiet); composite groups `LOUDS`/`STEADYS`/`QUIETS` (by tier) and `TODOS`/`FIXMES`/`HACKS`/`BUGS` (by kind) are pre-defined flag combinations

- `TriageTagType.find_first_in_line(line)` — first tag match in a line, or `None`
- `TriageTagType.filter_by_group(tags, group)` — keep only tags belonging to a group (e.g. `LOUDS`, `TODOS | STEADYS`)

### `ttg.tt_gating`

Triage tag (TT) gating — blocks commits that introduce annotation markers on protected branches.

**Public API**: `perform_triage_tags_gating(repo_root)` — detect current commit type via the top-level `commit_type` module, then gate on the tag tiers appropriate to that merge type

Gating policy by commit type:

- `FEATURE_FINISH` → gates `LOUDS`
- `VERSION_RELEASE` → gates `LOUDS | STEADYS`
- anything else → skipped, no gating

On a gated match, `_perform_triage_tags_by_filtering_group` builds a report (file name banners via `kamilog.gen_comment_banner_centered`, `"-"` fill) and raises `SystemExit(1)`.

`tt_gating` and `tt_detect` share one logger, `TTG_LOGGER_NAME` (`"HU.TTG"`), defined in `hupy/ttg/__init__.py` **before** the `from .tt_gating import ...` line — `tt_gating` imports `TTG_LOGGER_NAME` back from the package `__init__`, so the definition must precede the import or it fails with a circular-import `ImportError`. `commit_type` keeps its own separate logger (`"HU.commit_type"`).

### `cli`

Argument parser and entrypoint for the `hupy` command-line tool.

**Public API**: `cli_parser` (ArgumentParser) · `cli_subparser` (subparsers action)

- **main parser** — prog name and description sourced from `__package__` and module docstring
- **subcommand parsers** — registered at module load time in separate modules (`ttg/parser.py`, `pch/parser.py`); each owns its own argument setup and dispatch function
- **current subcommands**:
  - `triage_tag_gating` / `ttg` (alias) — calls `perform_triage_tags_gating(os.getcwd())` after applying `-v`/`-q` verbosity
  - `prepend_commit_header` / `pch` (alias) — calls `prepend_commit_header(os.getcwd())` after applying `-v`/`-q` verbosity
- **verbosity** — `-v`/`-q` flags apply to the shared `PROJ_LOGGER_NAME` (`"HU"`) root logger; child loggers (`"HU.TTG"`, `"HU.PCH"`, `"HU.commit_type"`) inherit this level since they set none of their own

Dispatch follows a standard pattern: subcommand dispatch functions receive the parsed `argparse.Namespace` and call the corresponding utility function.

### `kamilog`

Customized logging module vendored from [github.com/kami-lel/kamilog](https://github.com/kami-lel/kamilog) (v2.1.0).

Key entities:

- **`KamiLogger`** — `logging.Logger` subclass; adds `.enter()`, `.skip()`, `.succ()`, `.pass_()`, `.done()`, `.fail()` methods for six extra levels between standard ones
- **`AnsiColor` / `AnsiRenderer`** — TTY-aware 16-color ANSI support; coloring is a no-op when the stream is not a TTY
- **`_LogFormatEngine` / `_LogFormatter`** — builds `LEVEL source: message` lines with optional absolute or relative timestamps
- **`_DiffOnlyEngine`** — sliding-window diff compression; replaces repeated character runs with `〃\t` markers aligned to 8-column tab stops
- **`getLogger(name, *, datefmt, relative_to)`** — public factory; returns a `KamiLogger` with stdout handler (< WARNING) and stderr handler (≥ WARNING) pre-attached
- **`add_verbose_arguments(parser)` / `set_logging_level_by_verbosity(namespace)`** — argparse `-v`/`-q` verbosity helpers
- **comment banners (CB0~CB5)** — `gen_comment_banner_centered/left_just/right_just(content, padding, *, line_width=80)` pad a single line to `line_width` with a fill character (or int `1`~`5` preset: `#`/`=`/`*`/`+`/`-`); `gen_comment_banner_zero(lines, *, line_width=80)` boxes multiple lines with top/bottom `#` rulers
- **CLI** (`python -m hupy.kamilog ...`) — `comment_banner`/`cb <mode c|l|r> <padding>` reads one line from stdin and prints a padded banner; `comment_banner_zero`/`cb0` reads all lines from stdin and prints a boxed banner; both accept `-w/--line-width` and `-e/--stderr`
  - known gap: the CLI's `padding` argument is read as a raw string, so the documented int `1`~`5` preset shorthand (e.g. `cb c 1`) does not resolve to a fill character — pass the literal character (e.g. `cb c "#"`) instead

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
hupy/                             # installable package
  __init__.py                     # PROJ_LOGGER_NAME = "HU"
  __main__.py                     # `python -m hupy` entry point
  cli.py                          # argument parsing & dispatch
  commit_type.py                  # classify in-progress commits
  kamilog.py                      # vendored logging module (v2.1.0)
  pch/                            # Prepend Commit Header package
    __init__.py                   # PCH_LOGGER_NAME = "HU.PCH"
    parser.py                     # CLI parser for pch subcommand
    prepend_commit_header.py      # main function: rewrite COMMIT_EDITMSG
  ttg/                            # Triage Tag Gating package
    __init__.py                   # TTG_LOGGER_NAME = "HU.TTG"
    parser.py                     # CLI parser for ttg subcommand
    tt_detect.py                  # scan staged diffs for TT markers
    tt_gating.py                  # gate commits by TT tier
examples/
  pch/                            # 4 runnable PCH demo scripts (passes & skips)
  ttg/                            # 6 runnable TTG demo scripts (fail/pass/skip)
tests/
  commit_type_test.py             # 9 tests for get_current_commit_type
  pch/                            # PCH-specific tests
    conftest.py                   # shared `repo_dir` fixture, sys.path shim
    pch_helpers.py                # COMMIT_EDITMSG seed/read helpers
    pch-prepend_commit_header_skip_test.py
    pch-prepend_commit_header_feature_finish_test.py
    pch-prepend_commit_header_version_release_test.py
    pch-prepend_commit_header_error_test.py
  ttg/                            # TTG-specific tests
    conftest.py                   # shared `repo_dir` fixture
    prep_repo.py                  # scenario repo generator (CLI + importable)
    ttg-tt_detect_test.py
    ttg-tt_gating_feature_finish_test.py
    ttg-tt_gating_version_release_test.py
    ttg-tt_gating_non_merge_test.py
    ttg-tt_gating_regular_merge_test.py
    ttg-tt_gating_error_test.py
  testee/
    default_repo.bundle           # minimal git bundle fixture for repo cloning
    ttg/                          # per-scenario fixture files used by prep_repo.py
pyproject.toml
```

### Testing Infrastructure

- **pytest fixtures** (`repo_dir`) — path under `tmp_path` for the scenario repo, populated by `prep_repo.py`; fixtures are scoped per-test and auto-cleaned by `tmp_path`
- **git bundle fixture** (`tests/testee/default_repo.bundle`) — minimal single-file repo fixture; `prep_repo.py` clones it and dynamically constructs scenarios (branches, commits, MERGE_HEAD state, staged files from `tests/testee/ttg/*.py`)
- **`tests/ttg/prep_repo.py`** — shared between tests and `examples/ttg/*.bash` demos; also runnable standalone via `--scenario <name>`, printing the prepared repo path so demos can `cd` into it
- **test file naming** — nested-package modules follow `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py` (e.g. `hupy/ttg/tt_gating.py` → `tests/ttg/ttg-tt_gating_*_test.py`, split further by scenario group)
