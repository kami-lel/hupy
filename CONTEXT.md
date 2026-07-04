# hupy CONTEXT

*Last updated: 2026-07-05 — re-audited full source tree against docs; corrected stale status line (pch/improve_commit_message) and wrong `kamilog` level numbers (`ENTER`/`SKIP`/`SUCC`); noted in-code and README TODO/FIXME markers as gaps throughout Module Details; expanded the Hook Integration Model with the finalized design (tracked `scripts/hupy-hooks/` scripts per git hook stage, `core.hooksPath`, comment-toggle config, planned `hupy init` subcommand, rejected `.hupy.toml`/`pre-commit`-framework alternatives); restructured the `cli` module's subcommand tree to mirror git hook stage names (`pre-commit`/`prepare-commit-msg` groups with `start`/`end` stubs) and added the `setup` package for the new `init` subcommand stub*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type`, `kamilog`, `cli`, `pch` (Prepend Commit Header), and the `ttg` package (Triage Tag Gating) are implemented; `branch_protection` and `ensure_file_edited` are not yet started.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependency: `gitpython>=3.1`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | argument parsing, subcommand dispatch, CLI entrypoint |
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for Feature Finish and Version Release merges |
| `setup` | **stub** | `init` subcommand parser only; dispatch is `pass  # TODO` — no scaffolding/`core.hooksPath` logic yet |
| `ttg.tt_detect` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.tt_gating` | **implemented** | gate commits by triage tag presence on protected branches |
| `branch_protection` | not yet implemented | detect and block annotation markers by severity tier on protected branches; README also flags a related scenario, blocking *direct* (non-merge) commits to `main` |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit; a bash-era utility being ported, per the `# Todo reimplement ensure file modified` marker in `hupy/__init__.py` |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

**Decision**: consumers wire `hupy` into git with a plain bash script per hook stage, tracked in the consuming repo at `scripts/hupy-hooks/<hook-name>`, that calls the CLI directly in sequence. Since `ttg` and `pch` run at different git hook stages (see `cli` in Module Details), this is **two tracked files**, not one:

- `scripts/hupy-hooks/pre-commit` — calls `python -m hupy pre-commit start`, then `python -m hupy pre-commit triage-tag-gating`, then `python -m hupy pre-commit end`
- `scripts/hupy-hooks/prepare-commit-msg` — calls `python -m hupy prepare-commit-msg start`, then `python -m hupy prepare-commit-msg prepend-commit-header`, then `python -m hupy prepare-commit-msg end`

`git config core.hooksPath` looks for a file named exactly after the hook type in the target directory, which is why the file names above must match the git hook names precisely — and why the CLI's `pre-commit`/`prepare-commit-msg` subcommand groups (added to `cli.py` to match this) are named after the git hook stages rather than the tool names.

- **Config surface = the script itself.** There is no separate `.hupy.toml`/YAML/INI/env-var config file. A feature is enabled by its CLI-call line being present; a user disables a feature by commenting that line out. Execution order is simply the line order — both the toggle state and the sequence are visible by reading the file top to bottom, with no separate schema to keep in sync. The `start`/`end` stub subcommands bookending each stage exist for future cross-cutting setup/teardown (e.g. a banner around the whole stage's output); no behavior yet.
- **Calls the CLI, not internal functions.** The script invokes `python -m hupy <subcommand>` rather than importing `hupy.ttg`/`hupy.pch` Python functions directly, because the CLI subcommands are `hupy`'s stable, documented public interface — internal function signatures carry no such guarantee.
- **Tracked via `core.hooksPath`, not `.git/hooks/` directly.** `.git/hooks/` is never committed by git, so a script placed there is per-clone and invisible to teammates. Instead, the tracked `scripts/hupy-hooks/` directory is pointed to by `git config core.hooksPath scripts/hupy-hooks`, making the hook script (and any comment-toggles in it) a normal, reviewable, version-controlled file. Symlinking tracked files into `.git/hooks/` was considered and rejected — same one-time-setup burden as `core.hooksPath`, but fragile on Windows (requires symlink privileges/`core.symlinks`).
- **Planned `hupy init` CLI subcommand** (not yet implemented) to remove the manual setup step: runs `git config core.hooksPath scripts/hupy-hooks` and scaffolds `scripts/hupy-hooks/` from a template if missing, so onboarding a repo to `hupy` is one documented command instead of a git-config incantation a new contributor has to know or look up.
- **Enforcement caveat**: none of the above is enforceable, only convenient — git hooks are client-side and opt-in (`git commit --no-verify` bypasses them entirely, and a developer can simply never run `hupy init`). Guaranteed enforcement, if ever needed, requires a server-side mechanism (CI required-checks, branch protection, or a self-hosted server's `pre-receive` hook), independent of this model.

Rejected the `pre-commit`-framework route (pre-commit.com): it would add a hard dependency on an external hook manager (install, `.pre-commit-config.yaml`, `rev:` pinning) on top of `hupy` itself, plus its own packaging burden (`.pre-commit-hooks.yaml`, `language: python` entry points, `pass_filenames: false` on every hook since neither `ttg` nor `pch` accept positional file args, and a second `pre-commit install --hook-type prepare-commit-msg` for `pch` specifically since it needs that stage) — at odds with the *composable*/*simple defaults* principles above and with `hupy`'s bash-script origin. Wrapping `hupy` as a `.pre-commit-hooks.yaml` hook is technically easy and may be revisited later as an optional secondary path, but is not planned work; note it would not, by itself, solve configurability — `hupy`'s CLI today has no flags beyond `-v`/`-q`.

Rejected a declarative config file (`.hupy.toml` or similar) for now: it would require `hupy` to ship and maintain a config-loading module (parsing, validation, defaults-merging) that doesn't exist today, and TOML tables have no inherent execution order (would need an explicit `sequence = [...]` key to recover what the bash script's line order gives for free). The two implemented features (`ttg`, `pch`) are boolean and order-sensitive, which the comment-toggle script handles natively. **Revisit once `ensure_file_edited` is built** — its config is inherently tabular (file-pattern → required line-range pairs), which bash variables can only encode clumsily; that is the natural trigger point to reconsider a declarative config file rather than building one preemptively.

Not yet implemented: `examples/{pch,ttg}/*.bash` today are demo/test scripts (see Testing Infrastructure) run standalone for scenario walkthroughs, not the `scripts/hupy-hooks/` install-ready hook script described above; that script, the `core.hooksPath` setup, and the `hupy init` subcommand are all future work.

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

Not yet exposed as its own CLI subcommand (`# todo consider expose commit type as part of cli`) — currently only consumed internally by `pch` and `ttg`.

### `pch`

Prepend Commit Header — rewrites in-progress commit messages to prepend informational headers for merge commits.

**Public API**: `prepend_commit_header(repo_root)` — detect current commit type via the top-level `commit_type` module, then prepend an appropriate header and rewrite `.git/COMMIT_EDITMSG`

Header generation logic:

- `FEATURE_FINISH` merge → `"Feature Finish: <source-branch-name>"` + blank line + original message
- `VERSION_RELEASE` merge → `"Version Release"` + blank line + original message (no version number yet — `# Fixme get version` in `_gen_version_release_header_content`)
- all other commit types → file left untouched, no exception

The rewrite separates comment lines (starting with `#`) from content, placing all comments after the content block to preserve git's template comments. Non-destructive on failure: if the atomic write via `os.replace()` fails, the original file is untouched and the temporary file is cleaned up.

README flags a planned scenario not yet covered by `examples/pch/`/`tests/pch/`: keeping a feature branch up to date by merging `dev` back *into* it (as opposed to the Feature Finish direction, feature → `dev`).

### `ttg.tt_detect`

Scans staged git diffs for triage tag annotation markers.

**Public API**: `detect_triage_tags_in_staged_file(file_path, repo_root=None)` → `list[(TriageTagType, str)]` — runs `git diff --cached -- file_path`, and for every added (`+`) line, records the first matching tag and the line text

**`TriageTagType(Flag)`** — 12 members across 3 tiers × 4 kinds (`TODO`/`FIXME`/`HACK`/`BUG`), each matched case-sensitively (`TODO` loud, `Todo` steady, `todo` quiet); composite groups `LOUDS`/`STEADYS`/`QUIETS` (by tier) and `TODOS`/`FIXMES`/`HACKS`/`BUGS` (by kind) are pre-defined flag combinations

- `TriageTagType.find_first_in_line(line)` — first tag match in a line, or `None`
- `TriageTagType.filter_by_group(tags, group)` — keep only tags belonging to a group (e.g. `LOUDS`, `TODOS | STEADYS`)

Detection is a plain regex word-boundary match on the whole added line — it does not check whether the match sits inside a comment for the file's language (`# todo detect TT with respect of code comment by file type`), so a tag appearing in a string literal or non-comment context would still register.

### `ttg.tt_gating`

Triage tag (TT) gating — blocks commits that introduce annotation markers on protected branches.

**Public API**: `perform_triage_tags_gating(repo_root)` — detect current commit type via the top-level `commit_type` module, then gate on the tag tiers appropriate to that merge type

Gating policy by commit type:

- `FEATURE_FINISH` → gates `LOUDS`
- `VERSION_RELEASE` → gates `LOUDS | STEADYS`
- anything else → skipped, no gating

On a gated match, `_perform_triage_tags_by_filtering_group` builds a report (file name banners via `kamilog.gen_comment_banner_centered`, `"-"` fill) and raises `SystemExit(1)`. The reported lines are plain text — no highlighting on the matched tag itself yet (`# todo print gated TT in colored highlighting`).

`tt_gating` and `tt_detect` share one logger, `TTG_LOGGER_NAME` (`"HU.TTG"`), defined in `hupy/ttg/__init__.py` **before** the `from .tt_gating import ...` line — `tt_gating` imports `TTG_LOGGER_NAME` back from the package `__init__`, so the definition must precede the import or it fails with a circular-import `ImportError`. `commit_type` keeps its own separate logger (`"HU.commit_type"`).

### `cli`

Argument parser and entrypoint for the `hupy` command-line tool.

**Public API**: `cli_parser` (ArgumentParser) · `cli_subparser` (subparsers action)

The subcommand tree mirrors git hook stage names, so the CLI shape matches the `scripts/hupy-hooks/<hook-name>` scripts described in the Hook Integration Model — each stage group is the CLI grouping that a corresponding tracked hook script calls into line by line:

```
hupy init
hupy pre-commit [start | triage-tag-gating | end]
hupy prepare-commit-msg [start | prepend-commit-header | end]
```

- **main parser** — prog name and description sourced from `__package__` and module docstring
- **`init`** — registered by the `setup` package's `setup/parser.py` (`register_cli_init_parser`), mirroring the `ttg`/`pch` pattern of each subcommand area owning its own parser module; dispatch is a stub (`pass  # TODO`), not yet implemented
- **`pre-commit` / `prepare-commit-msg`** — each is a stage *group*, registered directly in `cli.py` (not delegated to a subpackage, since neither stage is itself a single tool): it creates the group parser (with its own `start`/`end` stub subcommands, also `pass  # TODO`) and its own nested subparsers action, then delegates registration of the one real tool per stage to that tool's own module:
  - `pre-commit triage-tag-gating` — registered by `ttg/parser.py`'s `register_cli_ttg_parser(subparser)`, called with the `pre-commit` group's subparsers action (not the top-level one); calls `perform_triage_tags_gating(os.getcwd())` after applying `-v`/`-q` verbosity
  - `prepare-commit-msg prepend-commit-header` — registered by `pch/parser.py`'s `register_cli_pch_parser(subparser)`, called with the `prepare-commit-msg` group's subparsers action; calls `prepend_commit_header(os.getcwd())` after applying `-v`/`-q` verbosity
  - invoking a stage group with no further subcommand (e.g. bare `hupy pre-commit`) prints that group's own help, mirroring how the root parser handles no subcommand at all
- **dispatch functions are always module-level**, never nested inside their `register_cli_*_parser` function — including the `pre-commit`/`prepare-commit-msg` group's own "no subcommand given" handler, which needs its parser instance to call `.print_help()`. Since that instance only exists once `add_parser()` runs inside the register function, it's threaded through via `parser.set_defaults(func=_pre_commit_main, parser=pre_commit_parser)` and read back as `args.parser` inside the module-level `_pre_commit_main(args)` — avoiding a closure defined inside the register function.
- **`start`/`end` stubs** exist per stage as placeholders for future cross-cutting setup/teardown (e.g. banner logging around the whole stage); no behavior yet
- **no aliases** — the previous flat top-level `ttg`/`pch` short aliases were dropped in this restructure; the full hyphenated names are the only way to invoke each tool now
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
| `ENTER` | 15 | entering a hook or test case |
| `SKIP` | 16 | skipping a hook or test case |
| `SUCC` | 17 | task or operation succeeded |
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
  setup/                          # init subcommand package (stub)
    __init__.py                   # SETUP_LOGGER_NAME = "HU.init"
    parser.py                     # CLI parser for init subcommand; dispatch is pass # TODO
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
