# hupy CONTEXT

*Last updated: 2026-07-06 — implemented the reversed Hook Integration Model in code: `hupy/setup/parser.py` was renamed to `hupy/setup/cli_init.py` and rewritten to write a default `.hupy.config.json` (copied from the packaged `hupy/config/.hupy.config.json` template) at the repo root, and to copy the two packaged `hupy/hook-stubs/{pre-commit,prepare-commit-msg}` stub scripts into the repo's actual hooks directory — resolved via a new `_resolve_hooks_dir()` helper that reads `core.hooksPath` via GitPython and falls back to `.git/hooks/`, no longer setting `core.hooksPath` itself; `-f`/`--force` now gates per-file hook-stub conflicts and the config file independently. The old `hupy/default-hupy-hooks/` template directory and `scripts/hupy-hooks/`/`core.hooksPath`-writing code are gone. `tests/setup/` was rewritten to match (hook-stub copy, config write, hooks-dir resolution, and end-to-end CLI suites — 25 tests); updated the status line, module table, Hook Integration Model, `setup` Module Details, Package Layout, and Testing Infrastructure accordingly (previous round: documented this design change ahead of implementation; before that, `setup`/`init` implemented the prior `scripts/hupy-hooks/`/`core.hooksPath` design; before that, re-audited source tree against docs and restructured `cli`'s subcommand tree to mirror git hook stages)*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type`, `kamilog`, `cli`, `pch` (Prepend Commit Header), `setup` (`init` subcommand), and the `ttg` package (Triage Tag Gating) are implemented; `branch_protection` and `ensure_file_edited` are not yet started.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependency: `gitpython>=3.1`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | argument parsing, subcommand dispatch, CLI entrypoint |
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for Feature Finish and Version Release merges |
| `setup` | **implemented** | `init` subcommand: copies default hook stub scripts into the repo's actual hooks directory and writes a default `.hupy.config.json` at the repo root |
| `ttg.tt_detect` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.tt_gating` | **implemented** | gate commits by triage tag presence on protected branches |
| `branch_protection` | not yet implemented | detect and block annotation markers by severity tier on protected branches; README also flags a related scenario, blocking *direct* (non-merge) commits to `main` |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit; a bash-era utility being ported, per the `# Todo reimplement ensure file modified` marker in `hupy/__init__.py` |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

**Decision**: `hupy init` sets a repo up with two artifacts:

1. A tracked, dot-prefixed config file at the repo root, **`.hupy.config.json`** (JSON) — the config surface: which features (`ttg`, `pch`, and future ones) are enabled, and in what order they run per hook stage. Being tracked/committed, it's reviewable and shared across clones the same way any other project file is. Default content is copied from the packaged `hupy/config/.hupy.config.json` template.
2. Two thin stub scripts copied into the repo's actual hooks directory: `pre-commit` and `prepare-commit-msg`, sourced from the packaged `hupy/hook-stubs/`. Each stub does nothing but invoke the corresponding CLI stage group — `python -m hupy pre-commit "$@"` / `python -m hupy prepare-commit-msg "$@"` — which then reads `.hupy.config.json` to decide what to run and in what order (config-reading side not yet implemented — see `setup` in Module Details).

- **Config surface = `.hupy.config.json`, not the hook script.** This reverses an earlier "config surface = the script itself" decision (see *Prior rejections* below). The hook stub is a fixed, content-free trampoline; enabling/disabling a feature and controlling its order both become a JSON edit, not a bash edit.
- **Dot-prefixed naming (`.hupy.config.json`, not `hupy.config.json`)**: chosen by analogy to the Python ecosystem's single-purpose tool-config dotfiles (`.flake8`, `.pylintrc`, `.coveragerc`, `.isort.cfg`), and specifically to `.pre-commit-config.yaml` — the closest sibling in the ecosystem (same domain: tracked, root-level git-hook-orchestration config) and the exact framework rejected below as a dependency. Visible top-level docs in this repo (`AGENTS.md`, `CHANGELOG.md`, `CONTEXT.md`) were considered as a naming precedent and rejected — those are human-authored prose meant to be read, not tool-consumed config.
- **Hooks directory is resolved, not fixed to `.git/hooks/`.** `hupy.setup.cli_init._resolve_hooks_dir(repo)` reads `core.hooksPath` via GitPython's `config_reader()` and joins it onto `repo.working_tree_dir` if set (resolving relative to the repo root; an absolute configured path is used as-is since `pathlib` path-joining drops the left side when the right side is absolute), otherwise falls back to `pathlib.Path(repo.git_dir) / "hooks"`. `--hooks-dir` overrides this resolution entirely. `init` itself never writes `core.hooksPath` — an earlier design's redirection-at-a-tracked-directory approach (see *Prior rejections*) is unnecessary now that the hook scripts carry no meaningful content of their own; the reviewable content lives in `.hupy.config.json` instead.
- **Per-file conflict checks, not directory-level.** `_copy_hook_stubs` only checks whether each individual target filename (`pre-commit`, `prepare-commit-msg`) already exists — not whether the hooks directory itself exists. `.git/hooks/` always exists after `git init` (populated with git's own `*.sample` files), so a directory-existence check would force `-f` on every default-path run; per-file checks let a fresh repo's first `init` succeed without `-f` while still protecting a real pre-existing hook.
- **Calls the CLI, not internal functions.** The stub invokes `python -m hupy <subcommand>` rather than importing `hupy.ttg`/`hupy.pch` Python functions directly, because the CLI subcommands are `hupy`'s stable, documented public interface.
- **`-f`/`--force` gates the hook stubs and the config file independently** — `_copy_hook_stubs` and `_write_default_config` each perform their own existence/`force` check, so (e.g.) a pre-existing config with fresh hooks still aborts on the config step even though the hooks were already written; `init` is not atomic across the two artifacts (mirrors the non-atomicity of the prior design between copying scripts and configuring `core.hooksPath`).
- **Enforcement caveat**: none of the above is enforceable, only convenient. Git hooks are client-side and opt-in (`git commit --no-verify` bypasses them entirely, and a developer can simply never run `hupy init`). Guaranteed enforcement, if ever needed, requires a server-side mechanism (CI required-checks, branch protection, or a self-hosted server's `pre-receive` hook), independent of this model.

#### Prior rejections

Kept for their still-relevant reasoning, though the decisions above have since reversed or replaced them:

An earlier design wired `hupy` into git with a plain bash script per hook stage, tracked in the consuming repo at `scripts/hupy-hooks/<hook-name>`, calling the CLI directly in sequence, with `git config core.hooksPath scripts/hupy-hooks` pointing git at that tracked directory (`git config core.hooksPath` looks for a file named exactly after the hook type in the target directory — why the CLI's `pre-commit`/`prepare-commit-msg` subcommand groups are named after the git hook stages, which is unchanged). Feature enable/disable was a comment-toggle on the CLI-call line inside that tracked script, and execution order was simply the line order. Symlinking tracked files into `.git/hooks/` was considered and rejected at the time — same one-time-setup burden as `core.hooksPath`, but fragile on Windows (requires symlink privileges/`core.symlinks`).

Rejected the `pre-commit`-framework route (pre-commit.com): it would add a hard dependency on an external hook manager (install, `.pre-commit-config.yaml`, `rev:` pinning) on top of `hupy` itself, plus its own packaging burden (`.pre-commit-hooks.yaml`, `language: python` entry points, `pass_filenames: false` on every hook since neither `ttg` nor `pch` accept positional file args, and a second `pre-commit install --hook-type prepare-commit-msg` for `pch` specifically since it needs that stage) — at odds with the *composable*/*simple defaults* principles above and with `hupy`'s bash-script origin. Wrapping `hupy` as a `.pre-commit-hooks.yaml` hook is technically easy and may be revisited later as an optional secondary path, but is not planned work.

Previously rejected a declarative config file (`.hupy.toml` or similar): the reasoning at the time was that it would require a config-loading module (parsing, validation, defaults-merging) that didn't exist, and that TOML tables have no inherent execution order (would need an explicit `sequence = [...]` key to recover what the bash script's line order gave for free). That rejection is reversed by the current design, which adopts `.hupy.config.json` as the config surface — the intent is for execution order to be expressed explicitly in JSON (e.g. an array per stage) rather than relied upon implicitly, though the schema itself isn't implemented yet (see `setup` in Module Details).

`examples/{pch,ttg}/*.bash` remain demo/test scripts (see Testing Infrastructure) run standalone for scenario walkthroughs — they are not, and were never meant to be, install-ready hook scripts, and this is unaffected by the redesign.

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

Implements the `init` CLI subcommand (`hupy/setup/cli_init.py`, renamed from `parser.py`): onboards a repository onto `hupy` by writing the two hook stubs and a default `.hupy.config.json`.

**Public API**: `register_cli_init_parser(cli_subparser)`

`_init_main(args)` flow, in order:

1. open the repo via `git.Repo(root_path, search_parent_directories=True)` — on `InvalidGitRepositoryError`/`NoSuchPathError`, `logger.exception(...)` then `raise SystemExit(1) from e`, **before** any filesystem writes happen
2. resolve `repo_root = pathlib.Path(repo.working_tree_dir)` — deliberately *not* the raw `root_path` argument, so that running `hupy init` from any subdirectory still anchors `hooks_dir`/`repo_root` at the true repository root
3. resolve `hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)` — see Hook Integration Model for `_resolve_hooks_dir`'s `core.hooksPath`/`.git/hooks` fallback logic
4. `_copy_hook_stubs(hooks_dir, force)` — `hooks_dir.mkdir(parents=True, exist_ok=True)` (no error if it already exists — see Hook Integration Model on why this is per-file, not directory-level), then for each file in `hupy/hook-stubs/`: if the target already exists, without `force` → `logger.error(...)` + `raise SystemExit(1)` (leaving that and any later files untouched); with `force`, `logger.warning(...)` then overwrites; otherwise `shutil.copy2` (preserves the executable bit)
5. `_write_default_config(repo_root, force)` — same existence/`force` pattern as step 4, but for a single file: `repo_root / ".hupy.config.json"`, copied from the packaged `hupy/config/.hupy.config.json` template via `shutil.copy2`

**CLI arguments**: `REPO_ROOT` (positional, optional, `type=pathlib.Path`, default=`pathlib.Path(os.getcwd())`) · `--hooks-dir HOOKS_DIR` (`type=pathlib.Path`, default `None` → resolved in step 3 above) · `-f`/`--force` (`store_true`, gates both step 4 and step 5) · `-v`/`-q` verbosity

Known gap: `REPO_ROOT`'s default is `pathlib.Path(os.getcwd())` evaluated once, when `register_cli_init_parser` runs at module-import time — not per invocation. In a long-lived process (or across a test session that imports `hupy.cli`/`hupy.setup.cli_init` once) this default is frozen to whatever the cwd was at first import, not the cwd at call time, despite the help text's "default=current working directory" implying otherwise. `tests/setup/` works around this by always passing `REPO_ROOT` explicitly rather than relying on the default.

Packaged templates: `hupy/hook-stubs/{pre-commit,prepare-commit-msg}` (thin `python -m hupy <stage> "$@"` wrappers, no `.bash` extension since git requires the exact hook name in the hooks directory) and `hupy/config/.hupy.config.json` (default config content), bundled via `[tool.setuptools.package-data]` in `pyproject.toml` (`hupy = ["hook-stubs/*", "config/.hupy.config.json"]`).

Not yet implemented: the CLI side that *reads* `.hupy.config.json` when `hupy pre-commit`/`hupy prepare-commit-msg` run — the stubs call through to those stage groups already, but nothing yet parses the config to decide which of `ttg`/`pch` to invoke or in what order; today that's still whatever's wired directly in `cli.py`. The packaged default template is currently just `{}` — its intended shape (a JSON array per stage, e.g. `{"pre-commit": ["triage-tag-gating"], ...}`, in the order features should run) is not yet encoded, since nothing consumes it yet.

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
- **`init`** — registered by the `setup` package's `setup/cli_init.py` (`register_cli_init_parser`), mirroring the `ttg`/`pch` pattern of each subcommand area owning its own parser module; see `setup` below for its implementation
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
  config/                         # default HUPy config template (packaged data)
    .hupy.config.json              # default content, currently `{}`
  hook-stubs/                     # default hook stub scripts (packaged data)
    pre-commit                    # thin wrapper: `python -m hupy pre-commit "$@"`
    prepare-commit-msg            # thin wrapper: `python -m hupy prepare-commit-msg "$@"`
  kamilog.py                      # vendored logging module (v2.1.0)
  pch/                            # Prepend Commit Header package
    __init__.py                   # PCH_LOGGER_NAME = "HU.PCH"
    parser.py                     # CLI parser for pch subcommand
    prepend_commit_header.py      # main function: rewrite COMMIT_EDITMSG
  setup/                          # init subcommand package
    __init__.py                   # SETUP_LOGGER_NAME = "HU.init"
    cli_init.py                   # CLI parser + implementation for init subcommand
  ttg/                            # Triage Tag Gating package
    __init__.py                   # TTG_LOGGER_NAME = "HU.TTG"
    parser.py                     # CLI parser for ttg subcommand
    tt_detect.py                  # scan staged diffs for TT markers
    tt_gating.py                  # gate commits by TT tier
docs/
  ttg_doc.md                      # placeholder — TODO TTG doc
  pch_doc.md                      # placeholder — TODO PCH doc
  hupy_config_doc.md               # placeholder — TODO write .hupy.config.json doc
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
    setup_helpers.py               # `run_init_cli`, `get_configured_hooks_path`,
                                    # `set_configured_hooks_path` helpers
    setup-cli_init_copy_hook_stubs_test.py
    setup-cli_init_write_default_config_test.py
    setup-cli_init_resolve_hooks_dir_test.py
    setup-cli_init_init_cli_test.py
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
- **`tests/setup/`** — unit tests for `_copy_hook_stubs`, `_write_default_config`, and `_resolve_hooks_dir` each get their own file (`setup-cli_init_copy_hook_stubs_test.py`, `setup-cli_init_write_default_config_test.py`, `setup-cli_init_resolve_hooks_dir_test.py`), calling the `hupy.setup.cli_init` functions directly; `setup-cli_init_init_cli_test.py` covers the CLI wiring end-to-end, since that's the other meaningful public surface (unlike `ttg`/`pch`, which test their public function directly without a separate CLI-wiring suite) — `setup_helpers.run_init_cli(args_list)` builds a standalone `init` subparser via `register_cli_init_parser` and dispatches through it, exercising `--hooks-dir`/`-f`/`-v`/`-q` the same way the real `hupy` CLI would; `git_repo_dir` (in `conftest.py`) gives a fresh `git.Repo.init`-ed repo rather than reusing `ttg`'s scenario-bucket fixtures, since `init` doesn't care about commit type or branch state. Tests always pass `REPO_ROOT` explicitly rather than relying on its default, since that default is frozen at module-import time (see `setup` in Module Details). 25 tests total.
