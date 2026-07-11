# hupy CONTEXT

*Last updated: 2026-07-12 — first stable release `1.0.0`. For the full change history see `CHANGELOG.md`; this file describes the current architecture, not its evolution.*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Package `HUPy` (import name `hupy`) · build `setuptools` · Python `>=3.10` · install `pip install -e ".[dev]"` · dependencies `GitPython>=3.1`, `pydantic>=2`, `json5>=0.9`.

Implemented: `cbm`, `bdc`, `ttg`, `pch`, `ver_grep`, `config_file`, `state`, `should_run_module`, `cli` (incl. `init`), `kamilog`. Not started: `ensure_file_edited` (a bash-era utility still to be ported, per the `# todo reimplement ensure file modified` marker in `hupy/__init__.py`).

## Architecture

Each utility is a standalone module in `hupy/`, callable from any git hook script. Cross-module edges: within `ttg`; `pch`/`ttg`/`bdc` → `cbm`; `cbm`/`ver_grep`/`bdc` → `config_file`; `bdc`/`ttg`/`pch` → `should_run_module`, which itself depends on `config_file` and `state`.

| Module | Responsibility |
|---|---|
| `cli` | CLI entrypoint, parsing/dispatch (`cli_main.py`); `init` + repo loading (`cli_init.py`); the `hook` group nesting the `pre-commit`/`prepare-commit-msg`/`post-commit` stage runners (`hook/`); `verify` (`cli_verify.py`); `set-verbosity`/`sv` (`cli_set_verbosity.py`); `skip-once`/`so` (`cli_skip_once.py`) |
| `cbm` | Commit/Branch/Merge — classify a branch name as a `BranchType` and an in-progress commit as a `CommitType` |
| `config_file` | `HupyConfigFile` pydantic schema for `.hupy.config.jsonc`, cached JSON5 loading resolved against an open `git.Repo`, and default-config copying |
| `state` | `HupyStateFile` pydantic schema for `hupy-state.json` (verbosity, one-time skips), path resolution inside `repo.git_dir`, atomic thread-/process-safe load-and-save |
| `should_run_module` | top-level gate combining a module's config `is_disabled` flag with its `skip_once` state flag into one run/skip decision |
| `kamilog` | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | prepend header lines to in-progress merge commit messages; several stamp a version via `ver_grep` |
| `ver_grep` | extract a branch's version string by regex over a configured version file at that branch's git tip; classify major/minor/patch bumps |
| `ttg` | Triage Tag Gating — scan staged diffs for triage tags and abort commits that introduce them on protected branches |
| `bdc` | Ban Direct Commit — block a commit made directly on a protected branch, while still allowing merges into it |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **mostly stateless** — relies on git state and file diffs; the one exception is `hupy-state.json` (transient operator intent — verbosity, one-time skips), kept out of the tracked, reviewable `.hupy.config.jsonc`
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

`hupy init` sets a repo up with two artifacts:

1. **`.hupy.config.jsonc`** — a tracked, dot-prefixed JSON5/JSONC file at the repo root. The config surface: which features are enabled and in what order they run per stage. Copied verbatim from the packaged asset `hupy/assets/.hupy.config.jsonc`, whose `//` comments document each field (the schema itself carries no defaults).
2. **Hook stubs** — thin `pre-commit`, `prepare-commit-msg`, and `post-commit` scripts copied from `hupy/assets/hook-stubs/` into the repo's hooks directory. Each stub only invokes its stage: `"<python>" -m hupy hook <stage>`.

Key decisions:

- **Config surface is the file, not the script.** The stub is a fixed trampoline; enabling/ordering a feature is a config edit, not a bash edit.
- **Dot-prefixed naming** by analogy to `.flake8`/`.pre-commit-config.yaml` (tracked, root-level tool config); `.jsonc` reflects JSON5 parsing so `//` comments can document fields.
- **Hooks directory is resolved, not fixed.** `_resolve_hooks_dir(repo)` reads `core.hooksPath` (joined onto the work tree, absolute paths used as-is), else falls back to `.git/hooks`; `--hooks-dir` overrides. `init` never writes `core.hooksPath`.
- **Per-file conflict checks.** `_copy_hook_stubs` checks each target filename, not the directory (which always exists after `git init`), so a fresh repo's first `init` needs no `-f`.
- **`HOOK_STUBS_DIR` is public** so `verify` can reuse it (alongside `_resolve_hooks_dir`) to confirm every packaged stub filename is present in the resolved hooks dir; it only checks filenames, not file content.
- **Interpreter path baked in at install time.** The stub template's `{{PYTHON}}` placeholder is substituted with `sys.executable`; a bare `python` on `PATH` is unreliable for hooks fired by an IDE that never sourced the venv. Consequence: re-run `hupy init --force` after moving the venv.
- **`-f`/`--force` gates the stubs and the config file independently** — `init` is not atomic across the two artifacts.
- **`post-commit`'s only config-driven feature is its `hb` bracket** — it otherwise exists to spend `skip_once` (`state_file.reset_for_next_commit()`) once the round has fully landed; clearing earlier (e.g. in `prepare-commit-msg`) would drop skips before `commit-msg`-adjacent tooling could observe them. Both the lead and trail `hb` brackets run before `reset_for_next_commit()`, so their commands still see the round's `skip_once` state.
- **Enforcement caveat**: git hooks are client-side and opt-in (`--no-verify` bypasses them). Guaranteed enforcement needs a server-side mechanism, out of scope here.

## Module Details

### `cbm`

Commit/Branch/Merge — classifies branch names and in-progress commits from git state.

**Public API** (`hupy/cbm/__init__.py`): `BranchType`, `CommitType`, `get_current_commit_type(repo)`, `get_source_branch(repo)`, `get_target_branch(repo)` — all take an open `git.Repo`.

- **`BranchType(Enum)`** — `FEATURE`/`DEV`/`MAIN`/`HOTFIX`/`RELEASE`/`USER`. `from_name(branch_name, repo)` classifies against the `cbm` config section in order: `dev_branch_name`→`DEV`, `main_branch_name`→`MAIN`, `hotfix_branch_prefix/`→`HOTFIX`, `release_branch_prefix/`→`RELEASE`, any other `/`→`USER`, else `FEATURE`.
- **`CommitType(Flag)`** — level 1 `MERGE`/`OTHER_COMMIT`; level 2 (under `MERGE`) the eight merge types plus `OTHER_MERGE`. `decide_commit_type(source, target)` maps a `(BranchType, BranchType)` pair via `_MERGE_TYPE_BY_BRANCH_PAIR`: `(FEATURE,DEV)`→`FEATURE_LANDING`, `(DEV,MAIN)`→`VERSION_RELEASE`, `(MAIN,DEV)`→`SYNC_BACKPORT`, `(DEV,FEATURE)`→`CATCH_UP`, `(HOTFIX,MAIN)`→`HOTFIX_RELEASE`, `(HOTFIX,DEV)`→`HOTFIX_BACKPORT`, `(RELEASE,MAIN)`→`RELEASE_CUT`, `(RELEASE,DEV)`→`RELEASE_BACKPORT`; any other pair → `OTHER_MERGE`. See `docs/cbm_doc.md` for the full tables and Mermaid graphs.
- **`get_current_commit_type(repo)`** in order: no `MERGE_HEAD`→`OTHER_COMMIT`; multi-line `MERGE_HEAD` (octopus)→`OTHER_MERGE`; SHA matching a remote tracking ref of the target (pull merge)→`OTHER_MERGE`; else classify source/target branches and `decide_commit_type`. Detached HEAD → `get_target_branch` returns `None`, handled without error.

The three lookup functions cache per `repo.git_dir`, so repeated calls (e.g. from both `pch` and `ttg`) hit git once. Repo construction/error handling is the caller's job. Not yet its own CLI subcommand (`# todo consider expose commit type as part of cli`).

### `pch`

Prepend Commit Header — rewrites in-progress merge commit messages to prepend an informational header.

**Public API**: `prepend_commit_header(repo, state_file)` — returns immediately if `should_run_module(repo, state_file, "pch")` is `False`; else detects the commit type via `cbm` and rewrites `.git/COMMIT_EDITMSG`. A `_HEADER_GENERATORS` dict keyed by `CommitType` holds one generator per merge type:

| `CommitType` | Header |
|---|---|
| `FEATURE_LANDING` | `Feature Landing: <source-branch>` |
| `VERSION_RELEASE` | `<bump><release-type>: <version>` (e.g. `Minor Prototype Release: 0.4.0`, `Alpha Release: 1.3.0-alpha.1`); falls back to `Version Release: <version>` or plain `Version Release` |
| `SYNC_BACKPORT` | `Sync Backport from: <version>` or `Sync Backport` |
| `CATCH_UP` | `Catch Up: <target-branch>` |
| `HOTFIX_RELEASE` | `<bump>Hotfix Release: <version>` or `Hotfix Release` |
| `HOTFIX_BACKPORT` | `Hotfix Backport from: <version>` or `Hotfix Backport` |
| `RELEASE_CUT` | `<bump>Release Cut: <version>` or `Release Cut` |
| `RELEASE_BACKPORT` | `Release Backport from: <version>` or `Release Backport` |

`<bump>` (`Major `/`Minor `/`Patch `/`""`) comes from `ver_grep.decide_version_update_type` comparing source vs target versions. `VERSION_RELEASE`'s `<release-type>` comes from `_get_release_type_word(version, pch_config)`, checked in order: only when the version's `major.minor.patch` core matches (a raw `re.match(r"^\d+\.\d+\.\d+", version)`, not the pattern in `_get_version_bump_prefix`) is `alpha_tag`/`beta_tag`/`release_candidate_tag` checked as a substring → Alpha/Beta/Release Candidate (each skipped if its tag is empty); else `enable_pre_alpha` + `0.9.z` → Pre-Alpha; else `enable_vertical_slice` + `0.5.z`–`0.9.z` → Vertical Slice; else any `0.x.z` → Prototype; else `>=1.0.0` → Stable; else `""` (triggers the plain fallback). Gating the tag check behind the semver-core match keeps an unparsable version (eg `v2024.07-rc1`) from matching a tag substring by coincidence and instead falling through to plain `Version Release: <version>`. `<bump>` is forced empty for Alpha/Beta/RC.

`OTHER_COMMIT`/`OTHER_MERGE` → file untouched. The rewrite moves `#` comment lines after the content block and writes atomically via `os.replace()`, leaving the original intact on failure.

### `config_file`

Schema, loading, and default-copying for `.hupy.config.jsonc`.

**Public API**: `CONFIG_LOGGER_NAME` (`__init__.py`) · `HupyConfigFile` (`config_file.py`) · `CONFIG_FILENAME`, `DEFAULT_CONFIG_ASSET`, `get_config_file_path(repo)` (`config_file_path.py`) · `load_hupy_config(repo)` (`load_config.py`) · `create_default_config_file(repo, force)` (`write_config.py`).

- **`HupyConfigFile(BaseModel)`** — `hupy_version: str`, plus nested sections `vg`/`ttg`/`cbm`/`pch`/`bdc`/`hb`. **No field carries a Python-side default** — every value comes from the file on disk; the shipped asset `hupy/assets/.hupy.config.jsonc` is the sole source of defaults. A `model_validator` warns (does not raise) when `hupy_version` mismatches `importlib.metadata.version("HUPy")`.
- **per-module `is_disabled: bool`** on `vg`/`ttg`/`pch`/`bdc`/`hb`; `ttg`/`pch`/`bdc` check it via `should_run_module`, `vg` reads it in its own validator only to suppress the unconfigured warning.
- **`_VerGrep`** (`vg`) — `is_disabled`, `version_file`, `version_line_pattern`. `is_unconfigured()` is `True` when either is blank; a validator warns (not raises) on an unconfigured-but-enabled `vg`.
- **`_Ttg`** — `is_disabled`, `disable_tt_detect_by_type`, `ignored_path_globs`.
- **`_Cbm`** — `main_branch_name`, `dev_branch_name`, `hotfix_branch_prefix`, `release_branch_prefix` (all `min_length=1`).
- **`_Pch`** — `is_disabled`, `enable_vertical_slice`, `enable_pre_alpha`, `alpha_tag`, `beta_tag`, `release_candidate_tag` (empty tag disables that recognition).
- **`_Bdc`** — `is_disabled`, `ban_commit_to_main`, `ban_commit_to_dev`, `ban_commit_to_branches`.
- **`load_hupy_config(repo)`** — reads `get_config_file_path(repo)`, parses with `json5.loads()`, validates, and caches per process; on `FileNotFoundError`/`ValidationError` logs and `raise SystemExit(1)`.
- **`create_default_config_file(repo, force)`** — `shutil.copyfile`s the packaged asset verbatim (same existence/`force` pattern as the hook stubs). Used by `hupy init`.

`# Fixme rework .jsonc comments, along w/ complete doc rewrite` marks a pending pass on the asset's field docs (which replaced the deleted `docs/hupy_config_doc.md`).

### `state`

Local, untracked process state for `hupy-state.json` — the one exception to *mostly stateless*. Mirrors `config_file`'s shape but resolves inside `.git`, so it is never committed or shared.

**Public API**: `STATE_LOGGER_NAME` · `HupyStateFile` · `STATE_FILENAME`, `get_state_file_path(repo)` · `open_state_file(repo)`.

- **`HupyStateFile(BaseModel)`** — `hooks_logger_verbosity: int = 1`, `skip_once: set[str]`. These carry real defaults (no shipped asset; a missing file is a normal first run).
- **`skip_once`** — a one-time module-skip set, *checked not consumed* by `should_run_module` (plain membership), so a flag stays set across every check within a round. `skip-once -u` removes entries.
- **`reset_for_next_commit()`** — empties `skip_once`; called only by `hook post-commit`, spending the set exactly once per round.
- **`get_state_file_path(repo)`** = `repo.git_dir / STATE_FILENAME` (inside `.git/`, unlike `get_config_file_path`).
- **`open_state_file(repo)`** — a context manager making read+write thread- and process-safe (in-process `threading.Lock` **and** an `fcntl.flock`'d `.lock` sibling); reads via `model_construct` (no validation, tolerant of hand edits), yields fresh defaults if absent, writes back atomically via `tempfile` + `os.replace` after the `with` block. Callers hold it open for their whole dispatch body, so one open+save cycle covers the invocation. Own logger `STATE_LOGGER_NAME` (`"HU.state"`), propagation disabled.

### `should_run_module`

Top-level module (`hupy/should_run_module.py`) centralizing the run/skip decision `bdc`/`ttg`/`pch` used to each make on their own.

**Public API**: `should_run_module(repo, state_file, module_abbr)` — returns `True` only if neither skip source fires: (1) `getattr(config, module_abbr).is_disabled` (checked first, cheap cached read); (2) `module_abbr in state_file.skip_once` (membership, not consumed). Config-disabled ordering means a disabled module never masks a pending `skip_once` flag — it stays queued for a round where the module is enabled. Both branches log via `logger.skip(...)` using a local `_MODULE_ABBR_TO_NAME` display map.

**Known gap**: only `bdc`/`ttg`/`pch`/`hb` call this. `vg` is skippable and mapped, so `hupy skip-once vg` writes the flag without error, but nothing consults it (`vg` has no standalone entry point — it's only invoked internally by `pch`).

### `ver_grep`

Reads a branch's version string by regex over a configured version file at that branch's git tip (not the working tree, which mid-merge holds only the target's possibly-conflicted content); consumed by `pch`.

**Public API** (`hupy/ver_grep/__init__.py`): `grep_source_branch_version(repo, state_file)` · `grep_target_branch_version(repo, state_file)` · `decide_version_update_type(source_version, target_version)`.

- The two grep functions take `repo`/`state_file`, gate on `should_run_module(repo, state_file, "vg")`, load the `vg` config, resolve their branch via `cbm`, read the version file at that ref via `repo.git.show(f"{ref}:{version_file}")`, and return the first capturing-group match. Flow: unconfigured, gated-off, file missing at tip, or no matching line → `warning` + return `""`.
- **`decide_version_update_type`** — parses `major.minor.patch` cores (ignoring suffixes), returns `"x"`/`"y"`/`"z"` for major/minor/patch or `""` if unparsable or not a bump. Not yet wired into `pch`; available for future use.
- Own logger `VER_GREP_LOGGER_NAME` (`"HU.VerGrep"`), propagation disabled.

### `ttg`

Triage Tag Gating — blocks commits that introduce annotation markers on protected branches. All modules share `TTG_LOGGER_NAME` (`"HU.TTG"`), defined in `__init__.py` **before** the re-export line to avoid a circular import.

- **`triage_tag_type`** — `TriageTagType(Flag)`, 12 members (3 tiers × 4 kinds), case-sensitive; composite groups `LOUDS`/`STEADYS`/`QUIETS` and `TODOS`/`FIXMES`/`HACKS`/`BUGS` checked via native `in`.
- **`comment_style`** — `get_comment_prefix_for_file(file_path)` → comment-leader token (`//`/`#`/`<!--`) or `None` for an unmapped extension (then TT matches anywhere in the line).
- **`detect_tt`** — `detect_triage_tags_in_staged_file(file_path, repo_root=None, disable_tt_detect_by_type=False)` → `list[(TriageTagType, str, int)]`; runs `git diff --cached`, records the first tag per added line. When type-aware, only a tag after the comment leader counts. `_TT_PATTERN` lives here; `report_tt` imports it back for highlighting.
- **`staged_files`** — `get_staged_file_paths(repo)` (`SystemExit(1)` on git error); `is_path_ignored(file_path, ignored_path_globs)` via `fnmatch`.
- **`report_tt`** — `report_gated_tags(filtered_results)` logs `fail`, renders a per-file comment banner highlighting each matched tag, then `SystemExit(1)`.
- **`gate_tt`** — `perform_triage_tags_gating(repo, state_file)`: returns early if `should_run_module(..., "ttg")` is `False`; else gates by commit type — `FEATURE_LANDING` → `LOUDS`, `VERSION_RELEASE` → `LOUDS | STEADYS`, anything else → skip. Orchestrates list → collect (filter by ignore globs + tier) → report.

### `bdc`

Ban Direct Commit — blocks a commit made directly on a protected branch while still allowing merges into it.

**Public API**: `ban_direct_commit(repo, state_file)` — wired into `hook pre-commit` ahead of `perform_triage_tags_gating`. Flow: early return if `should_run_module(..., "bdc")` is `False`; build `protected_branches` from `config.bdc.ban_commit_to_branches` plus `dev`/`main` per their `ban_commit_to_*` flags; `current_branch not in protected` → skip (covers detached HEAD); `MERGE in get_current_commit_type(repo)` → pass (any merge allowed); else `fail` + `SystemExit(1)`. Own logger `BDC_LOGGER_NAME` (`"HU.BDC"`).

### `cli`

Argument parser and entrypoint for `hupy`; a package (`hupy/cli/`) split by subcommand. Five top-level subcommands, the three git hook stages nested under `hook`:

```
hupy init
hupy hook pre-commit
hupy hook prepare-commit-msg
hupy hook post-commit
hupy verify
hupy skip-once (alias: so)
hupy set-verbosity (alias: sv)
```

- **`cli_main.py`** — main parser (`prog="hupy"`) and dispatch; imports each subcommand module's `register_*_parser`.
- **`init`** (`cli_init.py`) — onboards a repo via a `_INIT_STEPS` registry (`copy_hooks`, `create_config_file`); plain `hupy init` runs both, `--copy-hooks`/`--create-config-file` select one. Resolves `repo_root` from `repo.working_tree_dir` (so running from a subdir still anchors correctly). `_copy_hook_stubs` mkdir-p's the hooks dir, then per file: conflict without `-f` → `SystemExit(1)`, else substitute `{{PYTHON}}`→`sys.executable`, write, and `shutil.copymode` to preserve the executable bit.
- **`verify`** (`cli_verify.py`, alias `v`) — loads/validates `.hupy.config.jsonc` via `load_hupy_config`, greps the current version via `grep_version`, then `_verify_hook_stubs(repo)` checks every `HOOK_STUBS_DIR` filename exists in the repo's resolved hooks dir (content not compared), raising `SystemExit(1)` after logging one `fail` line per missing stub; each step logs `pass` on success. Shares `load_git_repo`/`REPO_PATH_HELP` with `init` but takes no `-f`.
- **`load_git_repo(repo_path)`** — `git.Repo(..., search_parent_directories=True)`; on invalid repo, `SystemExit(1)` before any writes. Used by `init`, `verify`, and `load_hupy_config`.
- **`hook`** (`hook/cli_hook.py`) — content-free group nesting the three stages; prints help when called bare.
  - **`hook pre-commit`** — builds the repo, opens `hupy-state.json`, applies verbosity atop `state_file.hooks_logger_verbosity`, then `ban_direct_commit` → `perform_triage_tags_gating`.
  - **`hook prepare-commit-msg`** — same pattern, then `prepend_commit_header`.
  - **`hook post-commit`** — same pattern, then the `hb` lead bracket, the `hb` trail bracket, then `state_file.reset_for_next_commit()`.
- **`set-verbosity`** (`sv`) — sets `state_file.hooks_logger_verbosity` from a positional `VERBOSITY` int (default `1`) as the baseline for later `hook`/`skip-once` runs.
- **`skip-once`** (`so`) — flags modules to skip next round. `SKIPPABLE_MODULE = ("vg", "ttg", "pch", "bdc", "hb")`; the `modules` positional accepts abbr or kebab-case full name, normalized then `skip_once.update(...)` (or `.difference_update(...)` with `-u`/`--unset`).
- Packaged templates `hupy/assets/hook-stubs/{pre-commit,prepare-commit-msg,post-commit}` and `hupy/assets/.hupy.config.jsonc` are bundled via `[tool.setuptools.package-data]`.

**Known gaps**: `REPO_PATH`'s default (`os.getcwd()`) is bound at module-import time, not per call — tests pass `REPO_PATH` explicitly. `SKIPPABLE_MODULE`/name maps are duplicated between `cli_skip_once.py` and `should_run_module.py` (different casing, same five abbrs), not yet factored out.

### `kamilog`

Customized logging vendored from [github.com/kami-lel/kamilog](https://github.com/kami-lel/kamilog) (v2.3.1).

- **`KamiLogger`** — `logging.Logger` subclass adding `.enter()`/`.skip()`/`.succ()`/`.pass_()`/`.done()`/`.fail()` for six extra levels.
- **`AnsiColor`/`AnsiRenderer`** — TTY-aware 16-color ANSI (no-op off a TTY).
- **`getLogger(name, *, datefmt=DATEFMT_TIME, relative_to=None)`** — factory returning a `KamiLogger` with stdout (<WARNING) and stderr (≥WARNING) handlers pre-attached.
- **`add_verbose_arguments(parser)`**; **`set_logging_level_by_namespace(...)`** (verbosity offset atop a base); **`set_logging_level_by_verbosity(...)`**.
- The `hook` stages call `set_logging_level_by_namespace(args, verbosity=state_file.hooks_logger_verbosity)`, targeting the shared `"HU"` root; child loggers (`"HU.TTG"`, `"HU.PCH"`, `"HU.CBM"`, `"HU.config-file"`, `"HU.VerGrep"`, `"HU.BDC"`, `"HU.state"`) set `propagate = False` and inherit the level.
- **comment banners** — `gen_comment_banner_centered/left_just/right_just(...)` and `gen_comment_banner_zero(...)`; CLI `python -m hupy.kamilog cb/cb0` reads stdin and prints padded/boxed banners. Known gap: the CLI's `padding` is read as a raw string, so the int `1`–`5` presets don't resolve — pass the literal character.

Custom levels (numeric): `ENTER` 15, `SKIP` 16, `SUCC` 17, `PASS` 21, `DONE` 25, `FAIL` 45.

## Annotation Markers

Gating operates on *triage tags* in three tiers — **Loud** (all-caps `TODO`/`FIXME`/`HACK`/`BUG`, blocked by default), **Steady** (title-case, configurable), **Quiet** (lowercase, configurable). Full taxonomy is in the global `CLAUDE.md` under **Triage Tags**.

## Package Layout

```
hupy/                             # installable package
  __init__.py                     # PROJ_LOGGER_NAME = "HU"
  __main__.py                     # `python -m hupy` entry point
  cli/                            # CLI package: parsing & dispatch
    cli_main.py                   # cli_parser/cli_subparser, registration
    cli_init.py                   # `init`; load_git_repo(repo_path)
    cli_verify.py                 # `verify` (alias `v`)
    cli_skip_once.py              # `skip-once`/`so`; SKIPPABLE_MODULE
    cli_set_verbosity.py          # `set-verbosity`/`sv`
    hook/                         # `hook` group: git hook stage runners
      cli_hook.py                 # nests the three stages below
      cli_pre_commit.py           # `hook pre-commit`
      cli_prepare_commit_msg.py   # `hook prepare-commit-msg`
      cli_post_commit.py          # `hook post-commit`: hb brackets + reset_for_next_commit()
  cbm/                            # Commit/Branch/Merge
    branch_type.py                # BranchType + from_name(branch_name, repo)
    commit_type.py                # CommitType + decide_commit_type(source, target)
    get_current_commit_type.py    # get_current_commit_type/get_source_branch/get_target_branch
  bdc/                            # Ban Direct Commit
    ban_direct_commit.py          # ban_direct_commit(repo, state_file)
  config_file/                    # config schema, load, write
    config_file.py                # HupyConfigFile + nested sections (no defaults)
    config_file_path.py           # CONFIG_FILENAME; DEFAULT_CONFIG_ASSET; get_config_file_path
    load_config.py                # load_hupy_config(repo): read JSON5 + validate, cache
    write_config.py               # create_default_config_file(repo, force)
  state/                          # hupy-state.json schema and I/O
    state_file.py                 # HupyStateFile: hooks_logger_verbosity, skip_once; reset_for_next_commit()
    state_file_path.py            # STATE_FILENAME; get_state_file_path (inside .git)
    open_state.py                 # open_state_file(repo): atomic, locked load+save
  should_run_module.py            # should_run_module(repo, state_file, module_abbr)
  assets/                         # packaged data
    .hupy.config.jsonc            # default config, commented; copied verbatim
    hook-stubs/{pre-commit,prepare-commit-msg,post-commit}  # `"{{PYTHON}}" -m hupy hook <stage>`
  kamilog.py                      # vendored logging (v2.3.1)
  pch/prepend_commit_header.py    # rewrite COMMIT_EDITMSG; _HEADER_GENERATORS
  ttg/                            # Triage Tag Gating
    triage_tag_type.py            # TriageTagType flag enum
    comment_style.py              # extension -> comment leader
    detect_tt.py                  # scan staged diffs, type-aware
    staged_files.py               # list staged, filter ignored globs
    report_tt.py                  # render/log gated findings
    gate_tt.py                    # gate by TT tier
  ver_grep/                       # version grepping
    ver_grep.py                   # grep_version(repo, state_file, ref): grep at a git ref
    branch_version.py             # grep_source_branch_version/grep_target_branch_version
    version_bump.py               # decide_version_update_type
docs/
  ttg_doc.md                      # TTG tiers & per-merge gating
  cbm_doc.md                      # CBM concepts + PCH headers + ver_grep API
                                  # (config field docs live in hupy/assets/.hupy.config.jsonc)
examples/
  hooks/                          # bash demos driving the real `hupy hook <stage>` CLI:
                                  # pre-commit, prepare-commit-msg, post-commit, all-hooks
                                  # (each preps its repo via tests/fixtures/prep_repo.py)
  pch/                            # __init__.py helpers + 16 demo scripts (7 vr-* Version Release)
  ttg/                            # __init__.py helpers + 6 demo scripts
  bdc/                            # __init__.py helpers + 3 demo scripts
tests/
  conftest.py                     # root `repo_dir` fixture (tmp_path / "repo")
  fixtures/                       # cross-suite fixtures (not package-specific)
    default_repo.bundle           # minimal git bundle
    prep_repo.py                  # scenario repo generator (CLI + importable); writes .hupy.config.jsonc
    config_fixture.py             # load_config_fixture(overrides): deep-merge onto shipped asset
  cbm/ vg/ cli/ config_file/ state/ should_run_module/ pch/ ttg/ bdc/  # per-module suites
.hupy.config.jsonc                # this repo dogfoods hupy on itself
pyproject.toml
```

### Testing Infrastructure

- **Fixtures** — the root `tests/conftest.py` defines `repo_dir` (under `tmp_path`, auto-cleaned), shared by every suite; `tests/cli/conftest.py`'s `git_repo_dir` builds on it. `tests/fixtures/config_fixture.py`'s `load_config_fixture(overrides)` builds a validated `HupyConfigFile` by deep-merging `overrides` onto the shipped default asset — the standard way to build config now that the schema carries no defaults.
- **Repo scenarios** — `tests/fixtures/prep_repo.py` clones `default_repo.bundle` and constructs branches/commits/merge state. Three builders: `prepare_repo(dest, scenario)` for the TTG/PCH `SCENARIOS` unit tests exercise; `prepare_repo_with_files(dest, bucket, files)` for an arbitrary manifest against a `COMMIT_BUCKET`; `prepare_demo_repo(dest, bucket)` for demo-only `DEMO_BUCKETS` (six merge types with no `tests/pch/` assertions yet) plus seven `release_*` buckets backing the `vr-*` scripts. Also runnable standalone (`--scenario`/`--demo-bucket` + `--dest`); the bash demos shell out to it. `prep_repo.py`'s `_write_config_file` copies the shipped `DEFAULT_CONFIG_ASSET` onto each scenario repo as an untracked `.hupy.config.jsonc`, then overwrites `vg.version_file`/`version_line_pattern` to `"setup.cfg"`/`r"version\s*=\s*(\S+)"` so every scenario's committed `setup.cfg` version resolves; callers that build a repo by hand (eg `examples/bdc/__init__.py`'s `prepare_demo_repo_on_branch`) must call `_write_config_file` themselves, or `should_run_module`'s config lookup errors with a missing-config-file log.
- **Demo helpers** — `examples/{pch,ttg,bdc}/__init__.py` hold the `sys.path` shim onto `tests/fixtures/` plus the repo-prep + library-call wrappers shared by that directory's `*-demo.py` scripts, pulled in with `from __init__ import ...` (a run script's own directory is auto-added to `sys.path`).
- **Test file naming** — mirrors source: `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py`, split further by scenario group (e.g. `hupy/ttg/gate_tt.py` → `tests/ttg/ttg-gate_tt_*_test.py`, `hupy/cbm/get_current_commit_type.py`'s three functions → `tests/cbm/grct/cbm-grct-*_test.py`). A top-level module with no package (`hupy/should_run_module.py`) gets its own directory, dropping the `<pkg>-` prefix. Suites needing shared fixtures `sys.path.insert(tests/fixtures)` in their `conftest.py`.
- **Coverage notes** — `ttg.staged_files`/`ttg.report_tt` are covered indirectly through `ttg-gate_tt_*` (the git-error path via `ttg-gate_tt_error_test.py`, which patches `subprocess.check_output`); `create_default_config_file` is exercised through `cli-cli_init_init_cli_test.py` (asserting the written file is byte-identical to the asset), with no dedicated test file. The six newer merge types have only `examples/pch/*-demo.py` scripts, no dedicated `tests/pch/` assertions yet. Suites patch each module's own `load_hupy_config` reference (bound per call site by `from ... import`).
