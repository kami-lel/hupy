# hupy CONTEXT

*Last updated: 2026-07-05 — reversed the Hook Integration Model: `hupy init` now writes a tracked, dot-prefixed `.hupy.config.json` (JSON, repo root) as the config surface, plus two thin stub scripts written directly into the untracked `.git/hooks/pre-commit`/`prepare-commit-msg` (no more tracked `scripts/hupy-hooks/` directory, no more `core.hooksPath`); the declarative-config rejection is superseded and the `core.hooksPath`-required-for-tracking rationale no longer applies since the config itself is what's tracked now. This is a **documented design change only** — `setup`'s code still implements the prior `scripts/hupy-hooks/` + `core.hooksPath` approach and has not been updated yet; updated the status line, module table, Hook Integration Model, `setup` Module Details, Package Layout, and Testing Infrastructure to flag this gap (previous rounds: `setup`/`init` implemented copying `hupy/default-hupy-hooks/` templates and setting `core.hooksPath`, covered by `tests/setup/`; before that, re-audited source tree against docs and restructured `cli`'s subcommand tree to mirror git hook stages)*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type`, `kamilog`, `cli`, `pch` (Prepend Commit Header), `setup` (`init` subcommand), and the `ttg` package (Triage Tag Gating) are implemented; `branch_protection` and `ensure_file_edited` are not yet started. `setup`'s implementation currently reflects a **superseded design** (see Hook Integration Model) — a redesign to a tracked `.hupy.config.json` plus `.git/hooks/` stubs is documented but not yet implemented in code.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependency: `gitpython>=3.1`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | argument parsing, subcommand dispatch, CLI entrypoint |
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for Feature Finish and Version Release merges |
| `setup` | **implemented (design superseded)** | `init` subcommand: currently copies the default hook script templates and configures `core.hooksPath` for a repo; redesign to write a tracked `.hupy.config.json` plus `.git/hooks/` stubs is documented but not yet implemented |
| `ttg.tt_detect` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.tt_gating` | **implemented** | gate commits by triage tag presence on protected branches |
| `branch_protection` | not yet implemented | detect and block annotation markers by severity tier on protected branches; README also flags a related scenario, blocking *direct* (non-merge) commits to `main` |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit; a bash-era utility being ported, per the `# Todo reimplement ensure file modified` marker in `hupy/__init__.py` |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

**Status**: this section documents the **current design** (superseding the prior `scripts/hupy-hooks/` + `core.hooksPath` model, kept below under *Superseded design* for its still-relevant rejections). **Not yet implemented** — `setup`'s code on disk still implements the superseded model; see `setup` in Module Details.

**Decision**: `hupy init` sets a repo up with two artifacts instead of one:

1. A tracked, dot-prefixed config file at the repo root, **`.hupy.config.json`** (JSON) — this is now the config surface: which features (`ttg`, `pch`, and future ones) are enabled, and in what order they run per hook stage. Being tracked/committed, it's reviewable and shared across clones the same way any other project file is.
2. Two thin stub scripts written directly into the untracked `.git/hooks/`: `.git/hooks/pre-commit` and `.git/hooks/prepare-commit-msg`. Each stub does nothing but invoke the corresponding CLI stage group — `python -m hupy pre-commit` / `python -m hupy prepare-commit-msg` — which then reads `.hupy.config.json` to decide what to run and in what order.

- **Config surface = `.hupy.config.json`, not the hook script.** This reverses the prior "config surface = the script itself" decision. The hook stub is now a fixed, content-free trampoline; enabling/disabling a feature and controlling its order both become a JSON edit, not a bash edit. This does mean `hupy` must now ship and maintain a config-loading path (parsing, validation, defaults) that didn't exist before — see *Superseded design* below for why that used to be considered not worth it.
- **Dot-prefixed naming (`.hupy.config.json`, not `hupy.config.json`)**: chosen by analogy to the Python ecosystem's single-purpose tool-config dotfiles (`.flake8`, `.pylintrc`, `.coveragerc`, `.isort.cfg`), and specifically to `.pre-commit-config.yaml` — the closest sibling in the ecosystem (same domain: tracked, root-level git-hook-orchestration config) and the exact framework rejected below as a dependency. Visible top-level docs in this repo (`AGENTS.md`, `CHANGELOG.md`, `CONTEXT.md`) were considered as a naming precedent and rejected — those are human-authored prose meant to be read, not tool-consumed config.
- **`.git/hooks/` directly, no `core.hooksPath` redirection.** The prior model avoided `.git/hooks/` because it's never tracked by git, so anything meaningful placed there (the toggle logic itself) would be invisible to teammates — hence redirecting `core.hooksPath` at a tracked directory. That problem is now solved differently: the hook *scripts* carry no meaningful content (just a fixed call-through), so it no longer matters that `.git/hooks/` itself isn't tracked — the actual reviewable content lives in the tracked `.hupy.config.json` instead. This removes the need for `core.hooksPath` entirely.
- **Calls the CLI, not internal functions.** Unchanged from the prior design: the stub invokes `python -m hupy <subcommand>` rather than importing `hupy.ttg`/`hupy.pch` Python functions directly, because the CLI subcommands are `hupy`'s stable, documented public interface.
- **`hupy init` CLI subcommand** (not yet implemented under this design — see `setup` in Module Details) is expected to: write a default `.hupy.config.json` if none exists (or refuse/`--force`-overwrite if one does, mirroring the prior `-f`/`--force` behavior), and write the two `.git/hooks/` stubs. No `core.hooksPath` configuration step remains.
- **Enforcement caveat**: unchanged — none of the above is enforceable, only convenient. Git hooks are client-side and opt-in (`git commit --no-verify` bypasses them entirely, and a developer can simply never run `hupy init`). Guaranteed enforcement, if ever needed, requires a server-side mechanism (CI required-checks, branch protection, or a self-hosted server's `pre-receive` hook), independent of this model.

#### Superseded design

The following was the prior decision (now replaced above), kept for its still-relevant rejections of alternatives:

Consumers used to wire `hupy` into git with a plain bash script per hook stage, tracked in the consuming repo at `scripts/hupy-hooks/<hook-name>`, calling the CLI directly in sequence, with `git config core.hooksPath scripts/hupy-hooks` pointing git at that tracked directory (`git config core.hooksPath` looks for a file named exactly after the hook type in the target directory — why the CLI's `pre-commit`/`prepare-commit-msg` subcommand groups are named after the git hook stages). Feature enable/disable was a comment-toggle on the CLI-call line inside that tracked script, and execution order was simply the line order. Symlinking tracked files into `.git/hooks/` was considered and rejected at the time — same one-time-setup burden as `core.hooksPath`, but fragile on Windows (requires symlink privileges/`core.symlinks`).

Rejected the `pre-commit`-framework route (pre-commit.com): it would add a hard dependency on an external hook manager (install, `.pre-commit-config.yaml`, `rev:` pinning) on top of `hupy` itself, plus its own packaging burden (`.pre-commit-hooks.yaml`, `language: python` entry points, `pass_filenames: false` on every hook since neither `ttg` nor `pch` accept positional file args, and a second `pre-commit install --hook-type prepare-commit-msg` for `pch` specifically since it needs that stage) — at odds with the *composable*/*simple defaults* principles above and with `hupy`'s bash-script origin. Wrapping `hupy` as a `.pre-commit-hooks.yaml` hook is technically easy and may be revisited later as an optional secondary path, but is not planned work.

Previously rejected a declarative config file (`.hupy.toml` or similar): the reasoning at the time was that it would require a config-loading module (parsing, validation, defaults-merging) that didn't exist, and that TOML tables have no inherent execution order (would need an explicit `sequence = [...]` key to recover what the bash script's line order gave for free). **This rejection is now reversed** — the current design (above) adopts `.hupy.config.json` as the config surface, with execution order expressed explicitly in the JSON structure rather than relied upon implicitly. The originally-cited trigger for revisiting (`ensure_file_edited`'s inherently tabular config) has not yet been reached; the reversal instead comes from wanting the config, not the hook script, to be the reviewable/version-controlled surface.

`examples/{pch,ttg}/*.bash` remain demo/test scripts (see Testing Infrastructure) run standalone for scenario walkthroughs — they are not, and were never meant to be, install-ready hook scripts, and this is unaffected by the redesign. The previously-described install-ready templates at `hupy/default-hupy-hooks/{pre-commit,prepare-commit-msg}.bash` are superseded in role: under the new design, any packaged template content would back the thin `.git/hooks/` stubs (and a default `.hupy.config.json`) rather than a full toggle script — see Package Layout for the current state of these files, which still contain their original placeholder content pending the redesign's implementation.

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

### `setup`

Implements the `init` CLI subcommand: onboards a repository onto `hupy`.

**Currently implemented (superseded design)** — copies the default hook scripts into a tracked `scripts/hupy-hooks/` directory and configures `core.hooksPath` to point at it:

**Public API**: `register_cli_init_parser(cli_subparser)`

`_init_main(args)` flow, in order:

1. open the repo via `git.Repo(root_path, search_parent_directories=True)` — on `InvalidGitRepositoryError`/`NoSuchPathError`, `logger.exception(...)` then `raise SystemExit(1) from e`, **before** any filesystem writes happen (so a bad target never leaves a half-created hooks dir)
2. resolve `repo_root = pathlib.Path(repo.working_tree_dir)` — deliberately *not* the raw `root_path` argument, so that running `hupy init` from any subdirectory still anchors `hooks_dir`/`core.hooksPath` at the true repository root
3. resolve `hooks_dir = args.hooks_dir or (repo_root / "scripts" / "hupy-hooks")`
4. `_copy_hooks_scripts(hooks_dir, force)` — creates `hooks_dir` if missing and copies every file from `hupy/default-hupy-hooks/` via `shutil.copy2` (preserves the executable bit); if `hooks_dir` already exists: without `-f`/`--force`, `logger.error(...)` + `raise SystemExit(1)` and the existing directory is left untouched; with `force`, `logger.warning(...)` then overwrites
5. `_configure_repo_hooks_path(repo, hooks_dir)` — `repo.config_writer().set_value("core", "hooksPath", str(hooks_dir))`; any failure is `logger.exception(...)` + `raise SystemExit(1) from e`

**CLI arguments**: `REPO_ROOT` (positional, optional, `type=pathlib.Path`, default=`pathlib.Path(os.getcwd())`) · `--hooks-dir HOOKS_DIR` (`type=pathlib.Path`, default `None` → resolved in step 3 above) · `-f`/`--force` (`store_true`) · `-v`/`-q` verbosity

Known gap: `REPO_ROOT`'s default is `pathlib.Path(os.getcwd())` evaluated once, when `register_cli_init_parser` runs at module-import time — not per invocation. In a long-lived process (or across a test session that imports `hupy.cli`/`hupy.setup.parser` once) this default is frozen to whatever the cwd was at first import, not the cwd at call time, despite the help text's "default=current working directory" implying otherwise. `tests/setup/` works around this by always passing `REPO_ROOT` explicitly rather than relying on the default.

Default hook script templates live at `hupy/default-hupy-hooks/{pre-commit,prepare-commit-msg}.bash` (see Hook Integration Model for their current placeholder-only content) and are bundled via `[tool.setuptools.package-data]` in `pyproject.toml` (`hupy = ["default-hupy-hooks/*.bash"]`).

**Designed, not yet implemented** — the redesigned flow (see Hook Integration Model) that this section's code is expected to move to:

1. resolve the repo root the same subdirectory-safe way as today (via `repo.working_tree_dir`)
2. write a default `.hupy.config.json` at the repo root if none exists — refusing (or `--force`-overwriting) if one is already present, mirroring today's existing/`-f` handling for `hooks_dir`
3. write the two hook stubs directly to `.git/hooks/pre-commit` and `.git/hooks/prepare-commit-msg` (each just invoking `python -m hupy pre-commit` / `python -m hupy prepare-commit-msg`), executable
4. no `core.hooksPath` configuration step — git already looks in `.git/hooks/` by default

The exact shape of `.hupy.config.json` (schema, defaults, how `ttg`/`pch` read it) is not yet designed beyond "tracks which features are enabled and their order per stage" — left open for when this is implemented.

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

The subcommand tree mirrors git hook stage names, so the CLI shape matches the `.git/hooks/<hook-name>` stub scripts described in the Hook Integration Model — each stage group is the CLI grouping that a corresponding hook stub calls into:

```
hupy init
hupy pre-commit [start | triage-tag-gating | end]
hupy prepare-commit-msg [start | prepend-commit-header | end]
```

- **main parser** — prog name and description sourced from `__package__` and module docstring
- **`init`** — registered by the `setup` package's `setup/parser.py` (`register_cli_init_parser`), mirroring the `ttg`/`pch` pattern of each subcommand area owning its own parser module; see `setup` below for its implementation
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
  default-hupy-hooks/              # default hook script templates (packaged data)
                                    # design change pending: content role shifts from
                                    # full toggle scripts to thin .git/hooks/ stubs
                                    # (see Hook Integration Model); not yet updated
    pre-commit.bash                # placeholder — TODO write default pre-commit.bash
    prepare-commit-msg.bash        # placeholder — TODO write default prepare-commit-msg.bash
  kamilog.py                      # vendored logging module (v2.1.0)
  pch/                            # Prepend Commit Header package
    __init__.py                   # PCH_LOGGER_NAME = "HU.PCH"
    parser.py                     # CLI parser for pch subcommand
    prepend_commit_header.py      # main function: rewrite COMMIT_EDITMSG
  setup/                          # init subcommand package
    __init__.py                   # SETUP_LOGGER_NAME = "HU.init"
    parser.py                     # CLI parser + implementation for init subcommand
  ttg/                            # Triage Tag Gating package
    __init__.py                   # TTG_LOGGER_NAME = "HU.TTG"
    parser.py                     # CLI parser for ttg subcommand
    tt_detect.py                  # scan staged diffs for TT markers
    tt_gating.py                  # gate commits by TT tier
docs/
  ttg_doc.md                      # placeholder — TODO TTG doc
  pch_doc.md                      # placeholder — TODO PCH doc
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
  setup/                          # setup (init subcommand) tests
    conftest.py                   # `repo_dir` / `git_repo_dir` fixtures
    setup_helpers.py               # `run_init_cli`, `read_hooks_path` helpers
    setup-parser_copy_hooks_scripts_test.py
    setup-parser_configure_hooks_path_test.py
    setup-parser_init_cli_test.py
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
- **`tests/setup/`** — unlike `ttg`/`pch` (which test their public function directly), `setup`'s meaningful public surface is the CLI wiring itself, so `setup_helpers.run_init_cli(args_list)` builds a standalone `init` subparser via `register_cli_init_parser` and dispatches through it, exercising `--hooks-dir`/`-f`/`-v`/`-q` the same way the real `hupy` CLI would; `git_repo_dir` (in `conftest.py`) gives a fresh `git.Repo.init`-ed repo rather than reusing `ttg`'s scenario-bucket fixtures, since `init` doesn't care about commit type or branch state. Tests always pass `REPO_ROOT` explicitly rather than relying on its default, since that default is frozen at module-import time (see `setup` in Module Details). These tests currently exercise the **superseded** `scripts/hupy-hooks/`/`core.hooksPath` behavior; they'll need rework once `init` moves to the `.hupy.config.json` + `.git/hooks/` stub design (see Hook Integration Model).
