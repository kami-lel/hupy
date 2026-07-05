# hupy CONTEXT

*Last updated: 2026-07-06 — folded the `setup` package into a new `cli` package (`hupy/setup/cli_init.py` → `hupy/cli/cli_init.py`, gaining an exported `load_git_repo(repo_path)`), and split the former flat `hupy/cli.py` into `cli/cli_main.py` (parser + registration) plus `cli/cli_pre_commit.py`/`cli/cli_prepare_commit_msg.py` (stage dispatch); added a `ver_grep` module (`grep_repo_version()`, regex-extracts a version string from a configured file) and a nested `_VerGrep` config sub-model (`ver_grep.version_file`/`version_line_pattern`, `is_unconfigured()`, warn-on-create validator), wired into `pch`'s Version Release header (`"Version Release: <version>"` when available); `config.load_config` renamed to `load_hupy_config`, now resolving the repo root via `load_git_repo` and caching the validated `HupyConfig` per process; hook stub templates switched from a bare `python -m hupy <stage> "$@"` to a `{{PYTHON}}` placeholder substituted with `sys.executable` at `init` time, fixing hooks failing under environments (e.g. an IDE's git integration) that don't source the project venv onto `PATH`. Updated the module table, Hook Integration Model, `cli`/`config` Module Details (folding the old `setup` section into `cli`), added a `ver_grep` Module Details section, Package Layout, and Testing Infrastructure accordingly (previous round: introduced a `config` package (`HupyConfig` pydantic model, `load_config`, `write_default_config`) so `.hupy.config.json` is generated from model defaults instead of a static template, and wired its `default_logger_verbosity` field into `cli.py`'s `pre-commit`/`prepare-commit-msg` dispatch via a new `kamilog.set_logging_level_by_namespace(namespace, *, verbosity=0, ...)`, while `set_logging_level_by_verbosity` was narrowed to take a plain int; also disabled logger propagation on `commit_type`, `pch.prepend_commit_header`, `setup.cli_init`, and `ttg.tt_gating`, and flattened the CLI subcommand tree; before that, implemented the reversed Hook Integration Model in code — `setup/parser.py` renamed to `setup/cli_init.py`, hook stubs and config copied into the repo from packaged templates, `tests/setup/` rewritten to match, 25 tests; before that, documented this design change ahead of implementation; before that, `setup`/`init` implemented the prior `scripts/hupy-hooks/`/`core.hooksPath` design; before that, re-audited source tree against docs and restructured `cli`'s subcommand tree to mirror git hook stages)*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **prototype** — `commit_type`, `kamilog`, `cli` (including `init`), `config`, `pch` (Prepend Commit Header), `ver_grep`, and the `ttg` package (Triage Tag Gating) are implemented; `branch_protection` and `ensure_file_edited` are not yet started.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependencies: `GitPython>=3.1`, `pydantic>=2`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself and `pch`'s use of `ver_grep`.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | CLI entrypoint, argument parsing/dispatch (`cli_main.py`); `init` subcommand and Git repo loading (`cli_init.py`); `pre-commit`/`prepare-commit-msg` stage runners (`cli_pre_commit.py`, `cli_prepare_commit_msg.py`) |
| `commit_type` | **implemented** | classify an in-progress commit as a `CommitType` enum member |
| `config` | **implemented** | `HupyConfig` pydantic schema for `.hupy.config.json` (including the nested `ver_grep` section), cached loading resolved against the Git repo root, and default-writing helpers |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for Feature Finish and Version Release merges; the latter appends a version number via `ver_grep` when configured |
| `ver_grep` | **implemented** | extract a repo's version string by regex-matching a line in a configured version file |
| `ttg.tt_detect` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.tt_gating` | **implemented** | gate commits by triage tag presence on protected branches |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit; a bash-era utility being ported, per the `# todo reimplement ensure file modified` marker in `hupy/__init__.py` |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

**Decision**: `hupy init` sets a repo up with two artifacts:

1. A tracked, dot-prefixed config file at the repo root, **`.hupy.config.json`** (JSON) — the config surface: which features (`ttg`, `pch`, and future ones) are enabled, and in what order they run per hook stage. Being tracked/committed, it's reviewable and shared across clones the same way any other project file is. Default content is generated from `HupyConfig` defaults (see `config` in Module Details), not copied from a static template.
2. Two thin stub scripts copied into the repo's actual hooks directory: `pre-commit` and `prepare-commit-msg`, sourced from the packaged `hupy/hook-stubs/`. Each stub does nothing but invoke the corresponding CLI stage group — `"<python>" -m hupy pre-commit` / `"<python>" -m hupy prepare-commit-msg` — which then reads `.hupy.config.json` via `load_hupy_config()`; today only `default_logger_verbosity` is consumed (feature enable/order fields aren't in `HupyConfig` yet — see `cli` and `config` in Module Details).

- **Config surface = `.hupy.config.json`, not the hook script.** This reverses an earlier "config surface = the script itself" decision (see *Prior rejections* below). The hook stub is a fixed, content-free trampoline; enabling/disabling a feature and controlling its order both become a JSON edit, not a bash edit.
- **Dot-prefixed naming (`.hupy.config.json`, not `hupy.config.json`)**: chosen by analogy to the Python ecosystem's single-purpose tool-config dotfiles (`.flake8`, `.pylintrc`, `.coveragerc`, `.isort.cfg`), and specifically to `.pre-commit-config.yaml` — the closest sibling in the ecosystem (same domain: tracked, root-level git-hook-orchestration config) and the exact framework rejected below as a dependency. Visible top-level docs in this repo (`AGENTS.md`, `CHANGELOG.md`, `CONTEXT.md`) were considered as a naming precedent and rejected — those are human-authored prose meant to be read, not tool-consumed config.
- **Hooks directory is resolved, not fixed to `.git/hooks/`.** `hupy.cli.cli_init._resolve_hooks_dir(repo)` reads `core.hooksPath` via GitPython's `config_reader()` and joins it onto `repo.working_tree_dir` if set (resolving relative to the repo root; an absolute configured path is used as-is since `pathlib` path-joining drops the left side when the right side is absolute), otherwise falls back to `pathlib.Path(repo.git_dir) / "hooks"`. `--hooks-dir` overrides this resolution entirely. `init` itself never writes `core.hooksPath` — an earlier design's redirection-at-a-tracked-directory approach (see *Prior rejections*) is unnecessary now that the hook scripts carry no meaningful content of their own; the reviewable content lives in `.hupy.config.json` instead.
- **Per-file conflict checks, not directory-level.** `_copy_hook_stubs` only checks whether each individual target filename (`pre-commit`, `prepare-commit-msg`) already exists — not whether the hooks directory itself exists. `.git/hooks/` always exists after `git init` (populated with git's own `*.sample` files), so a directory-existence check would force `-f` on every default-path run; per-file checks let a fresh repo's first `init` succeed without `-f` while still protecting a real pre-existing hook.
- **Calls the CLI, not internal functions.** The stub invokes `<python> -m hupy <subcommand>` rather than importing `hupy.ttg`/`hupy.pch` Python functions directly, because the CLI subcommands are `hupy`'s stable, documented public interface.
- **Interpreter path is baked in at install time, not resolved from `PATH`.** The packaged stub templates carry a `"{{PYTHON}}"` placeholder; `_copy_hook_stubs` substitutes it with `sys.executable` (the interpreter running `hupy init`) before writing each stub. A bare `python`/`python3` on `PATH` is unreliable for a git hook: hooks run in whatever environment invokes `git commit` — an IDE's built-in git integration, for instance, does not source the project's venv onto `PATH` — so a bare interpreter name can resolve to a system Python lacking both `hupy` and its dependencies (`ModuleNotFoundError: No module named 'git'`). Baking in the absolute path makes the hook work regardless of which client or shell state triggers the commit. A consequence: re-running `hupy init --force` is required after moving/recreating the virtualenv the package is installed in, since the old absolute path would otherwise go stale.
- **`-f`/`--force` gates the hook stubs and the config file independently** — `_copy_hook_stubs` and `write_default_config` each perform their own existence/`force` check, so (e.g.) a pre-existing config with fresh hooks still aborts on the config step even though the hooks were already written; `init` is not atomic across the two artifacts (mirrors the non-atomicity of the prior design between copying scripts and configuring `core.hooksPath`).
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
- `VERSION_RELEASE` merge → `_gen_version_release_header_content()` calls `ver_grep.grep_repo_version()`; if it returns a non-empty version string, the header is `"Version Release: <version>"`, otherwise plain `"Version Release"` (when `ver_grep` is unconfigured — see `ver_grep` in Module Details) + blank line + original message
- all other commit types → file left untouched, no exception

The rewrite separates comment lines (starting with `#`) from content, placing all comments after the content block to preserve git's template comments. Non-destructive on failure: if the atomic write via `os.replace()` fails, the original file is untouched and the temporary file is cleaned up.

README flags a planned scenario not yet covered by `examples/pch/`/`tests/pch/`: keeping a feature branch up to date by merging `dev` back *into* it (as opposed to the Feature Finish direction, feature → `dev`).

### `config`

Config schema, loading, and default-writing for `.hupy.config.json`.

**Public API**: `CONFIG_FILENAME` (`hupy/config/__init__.py`, `= ".hupy.config.json"`) · `CONFIG_LOGGER_NAME` (`= "HU.config-json"`) · `HupyConfig` (`model.py`) · `load_hupy_config(repo_path)` (`load_config.py`) · `write_default_config(repo_root, force)` (`write_config.py`)

- **`HupyConfig(BaseModel)`** — `hupy_version: str` (defaulted via `importlib.metadata.version("HUPy")`), `default_logger_verbosity: int = 1` (base verbosity `cli` passes into `set_logging_level_by_namespace` before `-v`/`-q` offsets apply), and `ver_grep: _VerGrep` (defaulted via `Field(default_factory=_VerGrep)`)
- **`_VerGrep(BaseModel)`** — `version_file: pathlib.Path` and `version_line_pattern: str`, both empty by default (see `ver_grep` in Module Details for how these are consumed). `is_unconfigured()` returns `True` when `version_file` is empty/`"."` (`pathlib.Path("")` normalizes to `.`) or `version_line_pattern` is blank. A `model_validator(mode="after")` calls `is_unconfigured()` on every instance creation and, if `True`, logs a `logger.warning(...)` via `CONFIG_LOGGER_NAME` rather than raising — an unconfigured `ver_grep` is a valid, non-fatal state (e.g. the default config `hupy init` writes)
- **`load_hupy_config(repo_path)`** — resolves the actual repo root via `hupy.cli.cli_init.load_git_repo(repo_path)` (so it works from any subdirectory, not just the root), reads and `HupyConfig.model_validate_json()`-validates `<repo_root> / CONFIG_FILENAME`; on `FileNotFoundError` or `pydantic.ValidationError`, logs and `raise SystemExit(1) from e` rather than propagating the exception. Caches the validated instance in a module-level `_config_cache` so the file is read from disk only once per process — repeated calls (e.g. from both `cli_pre_commit`/`cli_prepare_commit_msg` dispatch and `ver_grep.grep_repo_version`) return the same instance
- **`write_default_config(repo_root, force)`** — same existence/`force` conflict pattern as `_copy_hook_stubs` (see `cli` below), writing `HupyConfig().model_dump_json(indent=2) + "\n"`; used by `hupy init`, not by `load_hupy_config`
- no dedicated test suite yet (`# todo unit test for configs` in `hupy/config/__init__.py`); `write_default_config` is currently only exercised indirectly through `tests/cli/cli-cli_init_init_cli_test.py`

### `ver_grep`

Extracts a repo's version string by regex-matching a line in a configured version file; consumed by `pch` to append a version number to the Version Release commit header.

**Public API**: `grep_repo_version()` (no arguments — reads `.hupy.config.json` via `load_hupy_config(os.getcwd())`)

Flow, in order:

1. load config, read `config.ver_grep.version_file`/`version_line_pattern`
2. if `config.ver_grep.is_unconfigured()` → `logger.warning(...)` (asks the user to set `version_file`/`version_line_pattern` in the HUPy config file) and return `""` — a non-fatal, expected state, not an error
3. if `version_file` doesn't exist → `logger.error(...)` + `raise SystemExit(1)`
4. read the file, `re.search(pattern, line)` against each line in order; on the first match, return `match.group(1)` — the pattern **must** contain a capturing group
5. no line matches → `logger.error(...)` + `raise SystemExit(1)`

Own logger `VER_GREP_LOGGER_NAME` (`"HU.VerGrep"`, `hupy/ver_grep.py`), propagation disabled.

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

Argument parser and entrypoint for the `hupy` command-line tool; a package (`hupy/cli/`, formerly a flat `hupy/cli.py`) split by subcommand.

**Public API**: `cli_parser` (ArgumentParser) · `cli_subparser` (subparsers action) — both in `cli_main.py` · `register_cli_init_parser`/`load_git_repo` (`cli_init.py`) · `register_cli_pre_commit_parser` (`cli_pre_commit.py`) · `register_cli_prepare_commit_msg_parser` (`cli_prepare_commit_msg.py`)

The CLI has three top-level subcommands, mirroring the hook stages and setup:

```
hupy init
hupy pre-commit
hupy prepare-commit-msg
```

- **`cli_main.py`** — main parser and dispatch, unchanged in shape from the old `cli.py`: `prog="hupy"` (a literal string, not `__package__`, since this module now lives *inside* the `hupy.cli` package and `__package__` would otherwise resolve to `"hupy.cli"`), `description=__doc__`; imports each subcommand module's `register_*_parser` and calls them in turn against `cli_subparser`
- **`init`** — implemented in `cli_init.py` (moved from the former `hupy/setup/cli_init.py`); onboards a repository onto `hupy` by writing the two hook stubs and a default `.hupy.config.json`. `_init_main(args)` flow, in order:
  1. `repo = load_git_repo(args.repo_root)` — see `load_git_repo` below
  2. resolve `repo_root = pathlib.Path(repo.working_tree_dir)` — deliberately *not* the raw `args.repo_root`, so that running `hupy init` from any subdirectory still anchors `hooks_dir`/`repo_root` at the true repository root
  3. resolve `hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)` — see Hook Integration Model for `_resolve_hooks_dir`'s `core.hooksPath`/`.git/hooks` fallback logic
  4. `_copy_hook_stubs(hooks_dir, force)` — `hooks_dir.mkdir(parents=True, exist_ok=True)` (no error if it already exists — see Hook Integration Model on why this is per-file, not directory-level), then for each file in `hupy/hook-stubs/`: if the target already exists, without `force` → `logger.error(...)` + `raise SystemExit(1)` (leaving that and any later files untouched); with `force`, `logger.warning(...)` then overwrites; otherwise reads the template text, substitutes `{{PYTHON}}` with `sys.executable` (see Hook Integration Model), writes it, and `shutil.copymode` (preserves the executable bit, since the substitution is a text read/write rather than `shutil.copy2`)
  5. `write_default_config(repo_root, force)` (`hupy/config/write_config.py`) — same existence/`force` pattern as step 4, but for a single file: `repo_root / CONFIG_FILENAME`, generated from `HupyConfig().model_dump_json(indent=2)` rather than copied from a static template
- **`load_git_repo(repo_path)`** — `git.Repo(repo_path, search_parent_directories=True)`; on `InvalidGitRepositoryError`/`NoSuchPathError`, `logger.exception(...)` then `raise SystemExit(1) from e`, **before** any filesystem writes happen. Used by both `init` (via `_init_main`) and `config.load_hupy_config` (via `hupy.cli.cli_init.load_git_repo`), so both resolve the same way from any subdirectory of the repo
- **`init` CLI arguments**: `REPO_ROOT` (positional, optional, `type=pathlib.Path`, default=`pathlib.Path(os.getcwd())`) · `--hooks-dir HOOKS_DIR` (`type=pathlib.Path`, default `None` → resolved in step 3 above) · `-f`/`--force` (`store_true`, gates both step 4 and step 5) · `-v`/`-q` verbosity
- Known gap: `REPO_ROOT`'s default is `pathlib.Path(os.getcwd())` evaluated once, when `register_cli_init_parser` runs at module-import time — not per invocation. In a long-lived process (or across a test session that imports `hupy.cli.cli_init` once) this default is frozen to whatever the cwd was at first import, not the cwd at call time, despite the help text's "default=current working directory" implying otherwise. `tests/cli/` works around this by always passing `REPO_ROOT` explicitly rather than relying on the default
- Packaged templates: `hupy/hook-stubs/{pre-commit,prepare-commit-msg}` (thin `"{{PYTHON}}" -m hupy <stage>` wrappers, no `.bash` extension since git requires the exact hook name in the hooks directory), bundled via `[tool.setuptools.package-data]` in `pyproject.toml` (`hupy = ["hook-stubs/*"]`); `.hupy.config.json` is no longer a packaged file, since `write_default_config` generates its content from `HupyConfig` defaults instead of copying a template
- **`pre-commit`** (`cli_pre_commit.py`) — loads `.hupy.config.json` via `load_hupy_config(os.getcwd())`, applies `-v`/`-q` verbosity on top of `config.default_logger_verbosity`, then calls `perform_triage_tags_gating(os.getcwd())`; logs entry/exit via the logger (no nested subcommands)
- **`prepare-commit-msg`** (`cli_prepare_commit_msg.py`) — same config-load-then-verbosity pattern, then calls `prepend_commit_header(os.getcwd())`; logs entry/exit via the logger (no nested subcommands)
- **dispatch functions are module-level**, each in their own module (`cli_pre_commit._pre_commit_main`, `cli_prepare_commit_msg._prepare_commit_msg_main`) — they call the public functions from `ttg.tt_gating` and `pch.prepend_commit_header` directly, not via a CLI re-entry
- **verbosity** — both stage dispatch functions call `kamilog.set_logging_level_by_namespace(args, verbosity=config.default_logger_verbosity)`, so `.hupy.config.json`'s `default_logger_verbosity` sets the baseline and each `-v`/`-q` shifts it by one step; this targets the shared `PROJ_LOGGER_NAME` (`"HU"`) root logger, and child loggers (`"HU.TTG"`, `"HU.PCH"`, `"HU.commit_type"`, `"HU.config-json"`, `"HU.VerGrep"`) inherit the resulting level since they set none of their own. `cli_init.py`'s `init` calls the same function but without a config (`set_logging_level_by_namespace(args, logger=logger)`, base `verbosity=0`), since `init` runs before any `.hupy.config.json` exists

Dispatch follows a simple pattern: subcommand dispatch functions receive the parsed `argparse.Namespace`, load config where one exists, handle verbosity, and call the corresponding public utility function.

### `kamilog`

Customized logging module vendored from [github.com/kami-lel/kamilog](https://github.com/kami-lel/kamilog) (v2.3.1).

Key entities:

- **`KamiLogger`** — `logging.Logger` subclass; adds `.enter()`, `.skip()`, `.succ()`, `.pass_()`, `.done()`, `.fail()` methods for six extra levels between standard ones
- **`AnsiColor` / `AnsiRenderer`** — TTY-aware 16-color ANSI support; coloring is a no-op when the stream is not a TTY
- **`_LogFormatEngine` / `_LogFormatter`** — builds `LEVEL source: message` lines with optional absolute or relative timestamps
- **`_DiffOnlyEngine`** — sliding-window diff compression; replaces repeated character runs with `〃\t` markers aligned to 8-column tab stops
- **`getLogger(name, *, datefmt=DATEFMT_TIME, relative_to=None)`** — public factory; returns a `KamiLogger` with stdout handler (< WARNING) and stderr handler (≥ WARNING) pre-attached; timestamps on by default (`DATEFMT_TIME`, `HH:MM:SS`)
- **`add_verbose_arguments(parser)`** — adds `-v`/`-q` (`action="count"`) to an argparse parser
- **`set_logging_level_by_namespace(namespace, *, verbosity=0, logger=None, logger_name=None)`** — adds `namespace.verbose`/`namespace.quiet` counts as an offset atop a base `verbosity`, then sets the resulting level; this is what `cli/cli_main.py` and `cli/cli_init.py` call
- **`set_logging_level_by_verbosity(verbosity, *, logger=None, logger_name=None)`** — sets a logger's level directly from a plain verbosity int, no namespace involved
- loggers created via `getLogger()` in `commit_type`, `pch.prepend_commit_header`, `cli.cli_init`, `config.model` (`CONFIG_LOGGER_NAME`), `ver_grep`, and `ttg.tt_gating` each set `logger.propagate = False` — every logger already carries its own stdout/stderr handlers from `getLogger()`, so leaving propagation on would double-print every record through the root logger's handlers too
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
  cli/                            # CLI package: parsing & dispatch
    __init__.py
    cli_main.py                   # cli_parser/cli_subparser, subcommand registration
    cli_init.py                   # `init` subcommand; load_git_repo(repo_path)
    cli_pre_commit.py             # `pre-commit` dispatch
    cli_prepare_commit_msg.py      # `prepare-commit-msg` dispatch
  commit_type.py                  # classify in-progress commits
  config/                         # HUPy config schema, load, and write helpers
    __init__.py                   # CONFIG_FILENAME = ".hupy.config.json"; CONFIG_LOGGER_NAME
    model.py                      # HupyConfig pydantic model (schema + defaults); _VerGrep
    load_config.py                # load_hupy_config(repo_path): resolve repo root, read + validate, cache
    write_config.py               # write_default_config(repo_root, force)
  hook-stubs/                     # default hook stub scripts (packaged data)
    pre-commit                    # thin wrapper: `"{{PYTHON}}" -m hupy pre-commit`
    prepare-commit-msg            # thin wrapper: `"{{PYTHON}}" -m hupy prepare-commit-msg`
  kamilog.py                      # vendored logging module (v2.3.1)
  pch/                            # Prepend Commit Header package
    __init__.py                   # PCH_LOGGER_NAME = "HU.PCH"
    prepend_commit_header.py      # main function: rewrite COMMIT_EDITMSG
  ttg/                            # Triage Tag Gating package
    __init__.py                   # TTG_LOGGER_NAME = "HU.TTG"
    tt_detect.py                  # scan staged diffs for TT markers
    tt_gating.py                  # gate commits by TT tier
  ver_grep.py                     # grep_repo_version(): regex-extract version from a file
docs/
  ttg_doc.md                      # placeholder — TODO TTG doc
  pch_doc.md                      # placeholder — TODO PCH doc
  hupy_config_doc.md               # placeholder — TODO write .hupy.config.json doc
examples/
  pch/                            # 4 runnable PCH demo scripts (passes & skips)
  ttg/                            # 6 runnable TTG demo scripts (fail/pass/skip)
tests/
  commit_type_test.py             # 9 tests for get_current_commit_type
  ver_grep_test.py                # 11 tests for grep_repo_version
  cli/                            # cli (init subcommand + hook stub install) tests
    conftest.py                   # `repo_dir` / `git_repo_dir` fixtures
    cli_helpers.py                 # `run_init_cli`, `get_configured_hooks_path`,
                                    # `set_configured_hooks_path` helpers
    cli-cli_init_copy_hook_stubs_test.py
    cli-cli_init_resolve_hooks_dir_test.py
    cli-cli_init_init_cli_test.py
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
.hupy.config.json                 # this repo dogfoods hupy on itself
pyproject.toml
```

### Testing Infrastructure

- **pytest fixtures** (`repo_dir`) — path under `tmp_path` for the scenario repo, populated by `prep_repo.py`; fixtures are scoped per-test and auto-cleaned by `tmp_path`
- **git bundle fixture** (`tests/testee/default_repo.bundle`) — minimal single-file repo fixture; `prep_repo.py` clones it and dynamically constructs scenarios (branches, commits, MERGE_HEAD state, staged files from `tests/testee/ttg/*.py`)
- **`tests/ttg/prep_repo.py`** — shared between tests and `examples/ttg/*.bash` demos; also runnable standalone via `--scenario <name>`, printing the prepared repo path so demos can `cd` into it
- **test file naming** — nested-package modules follow `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py` (e.g. `hupy/ttg/tt_gating.py` → `tests/ttg/ttg-tt_gating_*_test.py`, split further by scenario group)
- **`tests/cli/`** (formerly `tests/setup/`, renamed with the `hupy/setup/` → `hupy/cli/` move) — unit tests for `_copy_hook_stubs` and `_resolve_hooks_dir` each get their own file (`cli-cli_init_copy_hook_stubs_test.py`, `cli-cli_init_resolve_hooks_dir_test.py`), calling the `hupy.cli.cli_init` functions directly; the copy-stubs file also covers the `{{PYTHON}}` → `sys.executable` substitution (placeholder replaced, baked path absolute, packaged templates still carry the placeholder — see `cli` in Module Details). `write_default_config` (in `hupy/config/write_config.py`) has no dedicated test file of its own (see `config` in Module Details) and is instead exercised via `cli-cli_init_init_cli_test.py`, which asserts the written file matches `HupyConfig().model_dump_json(indent=2) + "\n"`. `cli-cli_init_init_cli_test.py` covers the CLI wiring end-to-end, since that's the other meaningful public surface (unlike `ttg`/`pch`, which test their public function directly without a separate CLI-wiring suite) — `cli_helpers.run_init_cli(args_list)` (formerly `setup_helpers.py`) builds a standalone `init` subparser via `register_cli_init_parser` and dispatches through it, exercising `--hooks-dir`/`-f`/`-v`/`-q` the same way the real `hupy` CLI would; `git_repo_dir` (in `conftest.py`) gives a fresh `git.Repo.init`-ed repo rather than reusing `ttg`'s scenario-bucket fixtures, since `init` doesn't care about commit type or branch state. Tests always pass `REPO_ROOT` explicitly rather than relying on its default, since that default is frozen at module-import time (see `cli` in Module Details). 25 tests total.
- **`tests/ver_grep_test.py`** — top-level module test (mirrors `hupy/ver_grep.py` per the top-level naming convention, like `commit_type_test.py`); patches `hupy.ver_grep.load_hupy_config` to inject a stubbed `HupyConfig` rather than touching disk/git, covering capture-group matching, first-match-wins, not-configured returning `""`, and `SystemExit` on a missing file or no matching line. 11 tests total.
- **`tests/pch/pch-prepend_commit_header_version_release_test.py`** — patches `hupy.pch.prepend_commit_header.grep_repo_version` (rather than `load_hupy_config`, since the version-string plumbing is already covered by `tests/ver_grep_test.py`) to assert the two header shapes: plain `"Version Release"` when it returns `""`, `"Version Release: <version>"` otherwise (semver and non-semver strings). 18 tests total in this file's package.
