# hupy CONTEXT

*Last updated: 2026-07-18. This file describes the current architecture, not its evolution — for the full change history see `CHANGELOG.md`.*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Package `HUPy` (import name `hupy`) · build `setuptools` · Python `>=3.10` · install `pip install -e ".[dev]"` · dependencies `GitPython>=3.1`, `pydantic>=2`, `json5>=0.9`.

Implemented: `cbm`, `bdc`, `ttg`, `pch`, `ver_grep`, `config_file`, `state`, `should_run_module`, `stub`, `cli` (incl. `init`), `kamilog`. Not started: `ensure_file_edited` (a bash-era utility still to be ported, per the `# todo reimplement ensure file modified` marker in `hupy/__init__.py`).

## Architecture

Each utility is a standalone module in `hupy/`, callable from any git hook script. Cross-module edges: within `ttg`; `pch`/`ttg`/`bdc` → `cbm`; `cbm`/`ver_grep`/`bdc` → `config_file`; `bdc`/`ttg`/`pch` → `should_run_module`, which itself depends on `config_file` and `state`.

| Module | Responsibility |
|---|---|
| `cli` | CLI entrypoint, parsing/dispatch (`cli_main.py`); `init` + repo loading (`cli_init.py`); the generic hook stage runner (`cli_hook.py`) dispatching the `hook` group's seventeen stage modules (`hooks/`); `verify` (`cli_verify.py`); the generic `get`/`set`/`unset`/`info` accessor runner (`cli_accessors.py`) dispatching each key module under `accessors/` (`hupy-version`, `verbosity`, `skip-once`) |
| `cbm` | Commit/Branch/Merge — classify a branch name as a `BranchType` and an in-progress commit as a `CommitType` |
| `config_file` | `HupyConfigFile` pydantic schema for `.hupy.config.jsonc`, cached JSON5 loading resolved against an open `git.Repo`, and default-config copying |
| `state` | `HupyStateFile` pydantic schema for `hupy-state.json` (verbosity, one-time skips), path resolution inside `repo.git_dir`, atomic thread-/process-safe load-and-save |
| `should_run_module` | top-level gate combining a module's config `is_disabled` flag with its `skip_once` state flag into one run/skip decision |
| `stub` | render, write, and sync git hook stub scripts in a repo's hooks directory, driven by which hook names are currently demanded |
| `kamilog` | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | prepend header lines to in-progress merge commit messages; several stamp a version via `ver_grep` |
| `ver_grep` | extract a branch's version string by regex over a configured version file at that branch's git tip; classify major/minor/patch bumps |
| `ttg` | Triage Tag Gating — scan staged diffs for triage tags and abort commits that introduce them on protected branches |
| `bdc` | Ban Direct Commit — block a commit made directly on a protected branch, while still allowing merges into it |
| `hb` | Hook Bracket — run configured shell commands (`lead`/`trail`) around a hook stage, filtered by commit type |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **mostly stateless** — relies on git state and file diffs; the one exception is `hupy-state.json` (transient operator intent — verbosity, one-time skips), kept out of the tracked, reviewable `.hupy.config.jsonc`
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

`hupy init` sets a repo up with two artifacts:

1. **`.hupy.config.jsonc`** — a tracked, dot-prefixed JSON5/JSONC file at the repo root. The config surface: which features are enabled and in what order they run per stage. Copied verbatim from the packaged asset `hupy/assets/.hupy.config.jsonc`, whose `//` comments document each field (the schema itself carries no defaults).
2. **Hook stubs** — thin scripts, one per demanded git hook stage, rendered in-process by `hupy.stub.update_stubs` and written into the repo's hooks directory. Each stub invokes its stage and forwards git's own hook arguments: `"<python>" -m hupy hook <stage> "$@"`.

Key decisions:

- **Config surface is the file, not the script.** The stub is a fixed trampoline; enabling/ordering a feature is a config edit, not a bash edit.
- **Dot-prefixed naming** by analogy to `.flake8`/`.pre-commit-config.yaml` (tracked, root-level tool config); `.jsonc` reflects JSON5 parsing so `//` comments can document fields.
- **Hooks directory is resolved, not fixed.** `hupy.stub.update_stubs.resolve_hooks_dir(repo)` reads `core.hooksPath` (joined onto the work tree, absolute paths used as-is), else falls back to `.git/hooks`; `--hooks-dir` overrides. `init` never writes `core.hooksPath`.
- **Per-file conflict checks.** `hupy.stub.update_stubs.install_hook_stubs` checks each target filename, not the directory (which always exists after `git init`), so a fresh repo's first `init` needs no `-f`; it aborts on the first conflict, in demanded-name order, leaving the rest untouched.
- **Hook names come from demand, not a bundled asset directory.** `hupy.stub.names_by_demand.get_hook_names_by_demand(repo)` is the sole source of which stages get a stub; both `install_hook_stubs` and `verify_hook_stubs` consume it, so there is nothing left on disk to fall out of sync with. Demand is computed dynamically, not hardcoded: every stage module under `hupy.cli.hooks` is auto-discovered (`pkgutil.iter_modules`), and a stage is demanded when its config `hb` bracket is enabled and holds a `lead`/`trail` command (`_HbBracket.should_install_hook_stub()`), or its module defines `run_features`/`run_after`. A missing config file is treated as "nothing demanded by config" (falls back to the `run_features`/`run_after` check alone) rather than aborting.
- **`verify`'s stub check is a two-way diff, not existence-only.** `verify_hook_stubs` compares `get_hook_names_by_demand(repo)` against every file in the hooks dir that `_is_managed_stub` identifies as HUPy-managed (matched by its rendered `-m hupy hook <name>` line, so unrelated files like git's own `*.sample` hooks are ignored); by default it only warns on missing/unused, `-u`/`--update-hook-stubs` additionally adds/removes them, and `-u -f`/`--force` also regenerates every already-installed demanded stub.
- **Interpreter path baked in at install time.** Each stub is rendered from `_STUB_TEMPLATE` with `sys.executable` filled in directly — no on-disk template file or placeholder substitution; a bare `python` on `PATH` is unreliable for hooks fired by an IDE that never sourced the venv. Consequence: re-run `hupy init --force` (or `hupy verify -u -f`) after moving the venv.
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

**Public API**: `CONFIG_LOGGER_NAME` (`__init__.py`) · `HupyConfigFile` (`config_file.py`) · `CONFIG_FILENAME`, `DEFAULT_CONFIG_ASSET`, `get_config_file_path(repo)` (`config_file_path.py`) · `load_hupy_config(repo, allows_file_not_found=False)` (`load_config.py`) · `create_default_config_file(repo, force)` (`write_config.py`).

- **`HupyConfigFile(BaseModel)`** — `hupy_version: str`, plus nested sections `vg`/`cbm`/`bdc`/`ttg`/`pt`/`pch`/`hb`. **No field carries a Python-side default** — every value comes from the file on disk; the shipped asset `hupy/assets/.hupy.config.jsonc` is the sole source of defaults. A `model_validator` warns (does not raise) when `hupy_version` mismatches `importlib.metadata.version("HUPy")`.
- **per-module `is_disabled: bool`** on `vg`/`ttg`/`pt`/`pch`/`bdc`/`hb`; `ttg`/`pt`/`pch`/`bdc` check it via `should_run_module`, `vg` reads it in its own validator only to suppress the unconfigured warning.
- **`_VerGrep`** (`vg`) — `is_disabled`, `version_file`, `version_line_pattern`. `is_unconfigured()` is `True` when either is blank; a validator warns (not raises) on an unconfigured-but-enabled `vg`.
- **`_Ttg`** — `is_disabled`, `disable_tt_detect_by_type`, `ignored_path_globs`.
- **`_Cbm`** — `main_branch_name`, `dev_branch_name`, `hotfix_branch_prefix`, `release_branch_prefix` (all `min_length=1`).
- **`_Pt`** (`pt`) — `is_disabled`, `trails: list[_PaperTrail]`. Each `_PaperTrail` — `glob` (required), `allow_commit_types: CommitType = CommitType(0)` (parsed by the same `_merge_commit_type_names(names)` helper `_HbCmd` uses, warning and skipping any illegal name), `remark` (log heading only).
- **`_Pch`** — `is_disabled`, `enable_vertical_slice`, `enable_pre_alpha`, `alpha_tag`, `beta_tag`, `release_candidate_tag` (empty tag disables that recognition).
- **`_Bdc`** — `is_disabled`, `ban_commit_to_main`, `ban_commit_to_dev`, `ban_commit_to_branches`.
- **`load_hupy_config(repo, allows_file_not_found=False)`** — reads `get_config_file_path(repo)`, parses with `json5.loads()`, validates, and caches per process; on `FileNotFoundError` returns `None` if `allows_file_not_found`, else logs and `raise SystemExit(1)`. Any parse or schema failure (`ValueError`, which `pydantic.ValidationError` subclasses) always logs and `raise SystemExit(1)`, regardless of `allows_file_not_found`.
- **`create_default_config_file(repo, force)`** — `shutil.copyfile`s the packaged asset verbatim (same existence/`force` pattern as the hook stubs). Used by `hupy init`.

`# Fixme rework .jsonc comments, along w/ complete doc rewrite` marks a pending pass on the asset's field docs (which replaced the deleted `docs/hupy_config_doc.md`).

### `state`

Local, untracked process state for `hupy-state.json` — the one exception to *mostly stateless*. Mirrors `config_file`'s shape but resolves inside `.git`, so it is never committed or shared.

**Public API**: `STATE_LOGGER_NAME` · `HupyStateFile`, `ChainSession` · `STATE_FILENAME`, `get_state_file_path(repo)` · `open_state_file(repo)`.

- **`HupyStateFile(BaseModel)`** — `hooks_logger_verbosity: int = 1`, `skip_once: set[str]`, `chain_session: ChainSession`. These carry real defaults (no shipped asset; a missing file is a normal first run).
- **`skip_once`** — a one-time module-skip set, *checked not consumed* by `should_run_module` (plain membership), so a flag stays set across every check within the current chain. `skip-once -u` removes entries.
- **`ChainSession(BaseModel)`** — `chain_ppid: int | None = None` (the owning git process, the chain-session key), `expect_post_rewrite: bool = False` (set by `prepare-commit-msg` on an amend, read by `post-commit` to decide whether to yield). `is_active()` reports `chain_ppid is not None`; `reset()` returns both fields to their idle defaults.
- **`reset_for_next_chain()`** — empties `skip_once` and calls `chain_session.reset()`; called by `cli_hook.py`'s generic stage runner only when `chain_policy.is_chain_terminal` reports the current stage as its chain's true close, spending the set exactly once per chain (see `cli` below for which stage that is per chain type).
- **`get_state_file_path(repo)`** = `repo.git_dir / STATE_FILENAME` (inside `.git/`, unlike `get_config_file_path`).
- **`open_state_file(repo)`** — a context manager making read+write thread- and process-safe (in-process `threading.Lock` **and** an `fcntl.flock`'d `.lock` sibling); reads via `model_construct` (no validation, tolerant of hand edits), yields fresh defaults if absent, writes back atomically via `tempfile` + `os.replace` after the `with` block. Callers hold it open for their whole dispatch body, so one open+save cycle covers the invocation. Own logger `STATE_LOGGER_NAME` (`"HU.state"`), propagation disabled.

### `should_run_module`

Top-level module (`hupy/should_run_module.py`) centralizing the run/skip decision `bdc`/`ttg`/`pch` used to each make on their own.

**Public API**: `should_run_module(repo, state_file, module_abbr)` — returns `True` only if neither skip source fires: (1) `getattr(config, module_abbr).is_disabled` (checked first, cheap cached read); (2) `module_abbr in state_file.skip_once` (membership, not consumed — the set is spent later by `reset_for_next_chain()` at the chain's closing stage). Config-disabled ordering means a disabled module never masks a pending `skip_once` flag — it stays queued for a chain where the module is enabled. Both branches log via `logger.skip(...)` using a local `_MODULE_ABBR_TO_NAME` display map.

**Known gap**: only `bdc`/`ttg`/`pt`/`pch`/`hb` call this. `vg` is skippable and mapped, so `hupy set skip-once vg` writes the flag without error, but nothing consults it (`vg` has no standalone entry point — it's only invoked internally by `pch`).

### `stub`

Generates and syncs git hook stub scripts in a repo's hooks directory; consumed by `cli init`/`cli verify`. No on-disk template files — stub content is rendered in-process.

**Public API**: `resolve_hooks_dir(repo)`, `install_hook_stubs(repo, hooks_dir=None, force=False)`, `verify_hook_stubs(repo, hooks_dir=None, force=False, update=False)` (`update_stubs.py`) · `get_hook_names_by_demand(repo)` (`names_by_demand.py`) — the sole source of which stage names get a stub, computed dynamically per-repo rather than hardcoded.

- **`resolve_hooks_dir(repo)`** — reads `core.hooksPath` (joined onto the work tree), else falls back to `repo.git_dir / "hooks"`.
- **`install_hook_stubs(repo, hooks_dir, force)`** — `hooks_dir` defaults to `resolve_hooks_dir(repo)`; for each demanded name: write the stub when absent, or when present and `force` is set; otherwise abort with `SystemExit(1)` on the first conflict (in demanded-name order), leaving the rest untouched.
- **`verify_hook_stubs(repo, hooks_dir, force, update)`** — `hooks_dir` defaults to `resolve_hooks_dir(repo)`; diffs `get_hook_names_by_demand(repo)` against every file `_is_managed_stub` identifies as HUPy-managed. `update=False` (default) only warns on missing/unused stubs; `update=True` adds missing and removes unused, additionally regenerating every already-installed demanded stub when `force=True` too.
- **`get_hook_names_by_demand(repo)`** (`names_by_demand.py`) — `_iter_hook_stage_modules()` auto-discovers every submodule of `hupy.cli.hooks` via `pkgutil.iter_modules` that exposes a `HOOK_NAME` (excluding `cli_hook.py`, which now lives outside that package). Loads config via `load_hupy_config(repo, allows_file_not_found=True)` (a missing file means "nothing configured", not an error). A stage is demanded when `_is_hb_bracket_active` (HB enabled and its bracket's `lead`/`trail` non-empty) or the module defines `run_features`/`run_after`.
- **stub content** — `_write_stub` renders `_STUB_TEMPLATE` (`exec "<python>" -m hupy hook <stage> "$@"`) with `sys.executable` baked in, then `chmod 0o755`. `exec` (not a plain call) matters: it replaces the wrapping bash process rather than forking a child, so `python`'s parent stays the invoking git process itself — the stability `chain_policy.adopt_session`'s PPID-keyed session depends on. Re-run `hupy init --install-hook-stubs --force`/`hupy verify -u -f` to pick this up on an already-installed repo.
- Shares `STUB_LOGGER_NAME` (`"HU.stub"`, `__init__.py`), propagation disabled.

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

### `pt`

Paper Trail — requires that at least one file matching a configured glob was changed alongside the current commit/rebase; the sole feature wired into `pre-rebase`, and runs right after `ttg` in `pre-commit`/`pre-merge-commit`.

**Public API** (`hupy/pt/__init__.py`): `PT_LOGGER_NAME` · `perform_paper_trail(repo, state_file, hook_name, hooks_args=())`.

- **`perform_paper_trail`** — early return if `should_run_module(..., "pt")` is `False`; loads `config.pt.trails`, early return (with a `skip` log) if empty; else resolves the current commit type via `cbm` and the hook's changed-file set via `changed_files.get_changed_file_paths`, then checks each paper trail in order, aborting with `SystemExit(1)` on the first that both applies (`allow_commit_types` intersects the current `CommitType`, or is empty) and matches no changed path (`fnmatch.fnmatch`).
- **`changed_files.get_changed_file_paths(repo, hook_name, hooks_args=())`** — `pre-rebase` → range diff between `hooks_args[0]` (upstream) and `hooks_args[1]` (defaulting to `HEAD` when blank/absent) via `git diff --name-only <upstream>...<branch>`; every other hook → `git diff --cached --name-only` (the staged set, correct for both `pre-commit` and `pre-merge-commit`). Both paths `SystemExit(1)` on a `git.GitCommandError`.
- A paper trail's `remark`, or its underlined `glob` when blank, labels its log heading (`_renderer.color(..., AnsiStyle.UNDERLINE)`, mirroring `hb`'s `_HbCmd` heading fallback).
- Own logger `PT_LOGGER_NAME` (`"HU.PT"`), propagation disabled.

### `bdc`

Ban Direct Commit — blocks a commit made directly on a protected branch while still allowing merges into it.

**Public API**: `ban_direct_commit(repo, state_file)` — wired into `hook pre-commit` ahead of `perform_triage_tags_gating`. Flow: early return if `should_run_module(..., "bdc")` is `False`; build `protected_branches` from `config.bdc.ban_commit_to_branches` plus `dev`/`main` per their `ban_commit_to_*` flags; `current_branch not in protected` → skip (covers detached HEAD); `MERGE in get_current_commit_type(repo)` → pass (any merge allowed); else `fail` + `SystemExit(1)`. Own logger `BDC_LOGGER_NAME` (`"HU.BDC"`).

### `hb`

Hook Bracket — runs the `lead`/`trail` shell commands configured per hook stage in `.hupy.config.jsonc`.

**Public API**: `perform_hook_brackets(repo, state_file, hook_name, is_lead, hooks_args=())` (`perform_hook_brackets.py`) — early return if `should_run_module(..., "hb")` is `False`; resolves the `_HbBracket` for `hook_name` via `config.hb.get_bracket(hook_name)` (`SystemExit`-free `ValueError` on an unrecognized name, which cannot happen from the three wired hook stages); iterates `bracket.lead` or `bracket.trail`, skipping a `_HbCmd` whose `allow_commit_types` doesn't intersect the current `CommitType` (empty `allow_commit_types` always runs). `hooks_args` is the list of raw arguments git passed to the hook invocation (e.g. `prepare-commit-msg`'s commit-msg file path), forwarded from each `hook <stage>` CLI's `hook_args` positional.
- **`_HbCmd` fields** (`config_file.py`) — `cmd: str` (required); `remark: str = ""` (log heading, falls back to the underlined `cmd` when blank); `allow_commit_types: CommitType = CommitType(0)`; `allow_failure: bool = False`; `timeout: float | None = None` (seconds; `None` waits forever).
- **execution** (`_run_hb_cmd`) — builds `cmd` by joining `hb_cmd.cmd` with each `hooks_args` entry passed through `shlex.quote`, then `subprocess.run(cmd, shell=True, executable="/bin/bash", cwd=repo.working_tree_dir, env=os.environ.copy(), check=False, timeout=hb_cmd.timeout)`. Forcing `/bin/bash` (rather than the platform-default shell `shell=True` would otherwise pick) keeps bash-only syntax in a configured `cmd` working consistently with the bash hook stubs that invoke HUPy. `subprocess.TimeoutExpired` and a non-zero `result.returncode` are handled the same way: `allow_failure` → `warning` and continue (or `return`, for a timeout); otherwise `fail` + `SystemExit`.

### `cli`

Argument parser and entrypoint for `hupy`; a package (`hupy/cli/`) split by subcommand. `--version` prints the installed package version directly. Six top-level subcommands, seventeen git hook stages nested under `hook`, three accessor keys nested under each of `get`/`set`/`unset`/`info`:

```
hupy init
hupy hook pre-commit
hupy hook prepare-commit-msg
hupy hook commit-msg
hupy hook post-commit
hupy hook pre-merge-commit
hupy hook post-merge
hupy hook pre-rebase
hupy hook post-rewrite
hupy hook applypatch-msg
hupy hook pre-applypatch
hupy hook post-applypatch
hupy hook pre-auto-gc
hupy hook post-index-change
hupy hook sendemail-validate
hupy hook fsmonitor-watchman
hupy hook post-checkout
hupy hook pre-push
hupy verify
hupy get {hupy-version,verbosity,skip-once}
hupy set {verbosity,skip-once}
hupy unset {skip-once}
hupy info {hupy-version,verbosity,skip-once}
```

- **`cli_main.py`** — main parser (`prog="hupy"`) and dispatch; imports each subcommand module's `register_*_parser`.
- **`init`** (`cli_init.py`) — onboards a repo via a `_INIT_STEPS` registry (`install_hook_stubs`, `create_config_file`); plain `hupy init` runs both, `--install-hook-stubs`/`--create-config-file` select one. Resolves `repo_root` from `repo.working_tree_dir` (so running from a subdir still anchors correctly). Hook-stub install delegates to `hupy.stub.update_stubs.install_hook_stubs(repo, hooks_dir=args.hooks_dir, force=args.force)`, which resolves the hooks dir itself when `hooks_dir` is `None`; config-file creation still delegates to `create_default_config_file`.
- **`verify`** (`cli_verify.py`, alias `v`) — loads/validates `.hupy.config.jsonc` via `load_hupy_config`, greps the current version via `grep_version`, then delegates to `hupy.stub.update_stubs.verify_hook_stubs(repo, force=args.force, update=args.update_hook_stubs)` to check the resolved hooks dir against `get_hook_names_by_demand(repo)`; plain `verify` only reports drift, `-u`/`--update-hook-stubs` syncs it (add missing, remove unused), `-u -f`/`--force` also regenerates already-installed demanded stubs. Shares `load_git_repo`/`REPO_PATH_HELP` with `init`; hooks-dir resolution now lives in `hupy.stub.update_stubs.resolve_hooks_dir`, not `cli_init.py`.
- **`load_git_repo(repo_path)`** — `git.Repo(..., search_parent_directories=True)`; on invalid repo, `SystemExit(1)` before any writes. Used by `init`, `verify`, and `load_hupy_config`.
- **`hook`** (`hooks/`) — one file per git hook stage (seventeen: `pre-commit`, `prepare-commit-msg`, `commit-msg`, `post-commit`, `pre-merge-commit`, `post-merge`, `pre-rebase`, `post-rewrite`, `applypatch-msg`, `pre-applypatch`, `post-applypatch`, `pre-auto-gc`, `post-index-change`, `sendemail-validate`, `fsmonitor-watchman`, `post-checkout`, `pre-push`), dispatched through one generic runner in `cli_hook.py` (`hupy/cli/cli_hook.py` — a sibling of `hooks/`, not inside it, so `hupy.stub.names_by_demand`'s auto-discovery over `hooks/`'s submodules doesn't pick up the runner itself). Each stage module exposes only `HOOK_NAME`, plus up to two optional hooks: `run_features(repo, state_file, proj_logger, logger, hooks_args)` (real per-stage logic, run between the `hb` lead/trail brackets — a `HOOK_STAGE_NOOP` debug log substitutes when absent), `run_after(repo, state_file, proj_logger, logger)` (after the trail bracket, before the finish log). Neither the stage's help text nor its loggers are declared in the module: `cli_hook.py`'s private `_run_hook_stage(hook_name, args, *, features=None, after=None)` builds `logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + hook_name)` (`propagate = False`) per call and passes it, alongside the module-level `proj_logger = kamilog.getLogger(PROJ_LOGGER_NAME)`, into `features`/`after`; it is the single dispatch shared by every stage: builds the repo, opens `hupy-state.json`, applies verbosity atop `state_file.hooks_logger_verbosity`, adopts the chain session (`chain_policy.adopt_session(state_file.chain_session, os.getppid())` — a differing or absent PID reclaims the session as a fresh chain, reusing whatever `skip_once`/`expect_post_rewrite` state was left otherwise), and, only when `hook_name == "prepare-commit-msg"`, sets `chain_session.expect_post_rewrite = chain_policy.detect_amend(args.hook_args)` before the lead bracket (so it lands ahead of `post-commit`'s own decision later in the chain); then `hb` lead bracket → `features` (or noop log) → `hb` trail bracket → `after` → a per-stage `debug`-level finish log (`"{stage} stage Finished"`, downgraded from `done` — no longer chain-signal-worthy on its own); `hooks_args=args.hook_args` (a `hook_args` positional, `nargs="*"`, capturing whatever argv git itself passed to the hook script via the hook stub's `"$@"`) threads into both bracket calls and into `features` itself (e.g. `pt`'s `pre-rebase` range diff needs the upstream/branch args git passes that stage). Finally, `chain_policy.is_chain_terminal(hook_name, state_file.chain_session)` decides whether *this* stage is the one closing its chain — unconditionally for `post-merge`/`post-applypatch`/`post-rewrite` and every standalone hook, conditionally for `post-commit` (closes unless `expect_post_rewrite` is set, in which case the trailing `post-rewrite` closes instead), never for any other stage — and if so, logs the single per-chain `proj_logger.done("{} Finished".format(chain_policy.get_chain_label(hook_name)))` (e.g. `"Commit Chain Finished"`) and calls `state_file.reset_for_next_chain()`. Private `_register_hook_stage(hook_subparser, mod)` builds a `doc = "run {HOOK_NAME} stage hooks"` string, uses it as the subparser's `help`/`description`, and wires the subparser to `_run_hook_stage` via the module's optional attributes, looked up with `getattr(mod, "run_features"/"run_after", None)`; only `register_cli_hook_parser` (calling `_register_hook_stage` once per stage module, in the same grouping as the list above) is exported. Whether a stage module defines `run_features`/`run_after` also feeds `hupy.stub.names_by_demand.get_hook_names_by_demand`'s stub-demand check.
  - **`chain_policy.py`** — the chain-session policy, independent of any one stage module: `TERMINAL_ALWAYS` (the frozenset of stages that unconditionally close their chain), `adopt_session(session, ppid)`, `is_chain_terminal(hook_name, session)`, `get_chain_label(hook_name)` (terminal stage → doc chain name, e.g. `post-commit`/`post-rewrite` both → `"Commit Chain"`; a standalone hook labels itself), `detect_amend(hook_args)` (see the `cli` **Known gaps** below for its `-c`/`-C` false-positive).
  - **`hook pre-commit`** (`pre_commit.py`) — `run_features`: `ban_direct_commit` → `perform_triage_tags_gating` → `perform_paper_trail`.
  - **`hook prepare-commit-msg`** (`prepare_commit_msg.py`) — `run_features`: `prepend_commit_header`. (The amend-detection side effect on `chain_session` is applied by `cli_hook.py` itself, not this module — see above.)
  - **`hook post-commit`** (`post_commit.py`) — no `run_features`/`run_after` (noop-logged); the chain-close reset moved into `cli_hook.py`'s generic runner, since `post-commit` must sometimes *yield* the close to a following `post-rewrite`.
  - **`hook pre-merge-commit`** (`pre_merge_commit.py`) — `run_features`: `perform_triage_tags_gating` → `perform_paper_trail` — the other stage (besides `pre-commit`) where a merge commit can actually be created (a conflict-free auto-merge never visits `pre-commit`).
  - **`hook pre-rebase`** (`pre_rebase.py`) — `run_features`: `perform_paper_trail` alone, matching `hooks_args` (`<upstream> [<branch>]`) against the range about to be replayed rather than a staged diff.
  - The other twelve stages carry no logic of their own yet — each module is just `HOOK_NAME`, run through the `hb` brackets only.
- **`get`/`set`/`unset`/`info`** (`cli_accessors.py`) — a generic accessor layer over `hupy-state.json` keys. `register_cli_accessors_parser` builds the four verb parsers, then for each key module in `_ACCESSORS = (hupy_ver, verbosity, skip_once)` nests a subparser named `mod.KEY` under every verb the module implements (`_register_accessor_op` checks `getattr(mod, "run_" + op_name, None)`); `set`/`unset` subparsers take a `VALUE` positional (`nargs="*"`). Dispatch (`_run_accessor`) opens the repo and state file, applies verbosity, and calls the module's `run_{get,set,unset,info}(repo, state_file, logger, args)`.
  - **`hupy-version`** (`accessors/hupy_ver.py`) — read-only; `run_get` prints `importlib.metadata.version("HUPy")`. No `run_set`/`run_unset`, so `set`/`unset` don't get a `hupy-version` subcommand.
  - **`verbosity`** (`accessors/verbosity.py`) — `run_get` prints `state_file.hooks_logger_verbosity`; `run_set` takes `VALUE[0]` (int, or the `HupyStateFile` schema default `1` with no `VALUE`) then offsets it by that same invocation's `-v`/`-q` count (`base + args.verbose - args.quiet`) before persisting.
  - **`skip-once`** (`accessors/skip_once.py`) — flags modules to skip next round. `SKIPPABLE_MODULE = ("vg", "ttg", "pt", "pch", "bdc", "hb")`; `run_set`/`run_unset` accept abbr or kebab-case full name via `_resolve_abbrs`, then `skip_once.update(...)`/`.difference_update(...)`; `run_set` with no `VALUE` clears the set instead of erroring, `run_unset` with no `VALUE` errors.
- The packaged default config `hupy/assets/.hupy.config.jsonc` is bundled via `[tool.setuptools.package-data]`; hook stubs carry no bundled asset — they are rendered in-process by `hupy.stub.update_stubs` (see the `stub` module details above).

**Known gaps**: `REPO_PATH`'s default (`os.getcwd()`) is bound at module-import time, not per call — tests pass `REPO_PATH` explicitly. `SKIPPABLE_MODULE`/name maps are duplicated between `accessors/skip_once.py` and `should_run_module.py` (different casing, same six abbrs), not yet factored out.

`hupy/cli/chain_policy.py`'s `detect_amend(hook_args)` reads `prepare-commit-msg`'s `<msg_file> <source> [<sha>]`: `source == "commit"` is git's signal for **three** distinct flags (`--amend`, `-c <commit>`, `-C <commit>`), only the first of which actually triggers a trailing `post-rewrite`; the heuristic over-predicts on the other two, so `post-commit` silently yields and no `Commit Chain Finished` ever prints for that chain (self-corrects on the *next* chain's `adopt_session`, so it's cosmetic, not a correctness bug — currently marked `# fixme` in-code, Quiet tier). Planned fix (pattern **A**, not yet implemented): add `hupy/cli/proc_argv.py` with `read_process_argv(pid) -> list[str] | None` (`/proc/<pid>/cmdline`, NUL-split; open question whether to add a `ps -o args= -p <pid>` fallback for non-Linux, or accept Linux-only and let non-Linux silently keep today's heuristic) and widen `detect_amend(hook_args, ppid=None)` to check `"--amend" in read_process_argv(ppid)` when available, falling back to the `hook_args` heuristic only when `ppid` is omitted or the read fails. `cli_hook.py` already computes `os.getppid()` once at session-adopt time (Step 3 of the plan reuses that value rather than calling it twice).

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
    cli_accessors.py              # generic get/set/unset/info runner + register_cli_accessors_parser
    accessors/                    # one module per accessor KEY
      hupy_ver.py                     # `hupy-version` (get/info only)
      verbosity.py                    # `verbosity` (get/set/info)
      skip_once.py                    # `skip-once` (get/set/unset/info); SKIPPABLE_MODULE
    cli_hook.py                   # generic _run_hook_stage/_register_hook_stage + register_cli_hook_parser; proj_logger; dynamic doc
    hooks/                        # `hook` group: one module per git hook stage
      pre_commit.py                    # run_features: ban_direct_commit + perform_triage_tags_gating + perform_paper_trail
      prepare_commit_msg.py            # run_features: prepend_commit_header
      commit_msg.py                    # HOOK_NAME only (hb brackets)
      post_commit.py                   # run_after: reset_for_next_commit
      pre_merge_commit.py              # run_features: perform_triage_tags_gating + perform_paper_trail
      post_merge.py                    # HOOK_NAME only (hb brackets)
      pre_rebase.py                    # run_features: perform_paper_trail
      post_rewrite.py                  # HOOK_NAME only (hb brackets)
      applypatch_msg.py                # HOOK_NAME only (hb brackets)
      pre_applypatch.py                # HOOK_NAME only (hb brackets)
      post_applypatch.py               # HOOK_NAME only (hb brackets)
      pre_auto_gc.py                   # HOOK_NAME only (hb brackets)
      post_index_change.py             # HOOK_NAME only (hb brackets)
      sendemail_validate.py            # HOOK_NAME only (hb brackets)
      fsmonitor_watchman.py            # HOOK_NAME only (hb brackets)
      post_checkout.py                 # HOOK_NAME only (hb brackets)
      pre_push.py                      # HOOK_NAME only (hb brackets)
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
  stub/                           # git hook stub script generation & sync
    __init__.py                   # STUB_LOGGER_NAME
    names_by_demand.py            # get_hook_names_by_demand(repo): auto-discovers hooks/ modules
    update_stubs.py               # resolve_hooks_dir/install_hook_stubs/verify_hook_stubs
  assets/                         # packaged data
    .hupy.config.jsonc            # default config, commented; copied verbatim
  kamilog.py                      # vendored logging (v2.3.1)
  pch/prepend_commit_header.py    # rewrite COMMIT_EDITMSG; _HEADER_GENERATORS
  ttg/                            # Triage Tag Gating
    triage_tag_type.py            # TriageTagType flag enum
    comment_style.py              # extension -> comment leader
    detect_tt.py                  # scan staged diffs, type-aware
    staged_files.py               # list staged, filter ignored globs
    report_tt.py                  # render/log gated findings
    gate_tt.py                    # gate by TT tier
  pt/                              # Paper Trail
    __init__.py                   # PT_LOGGER_NAME
    changed_files.py               # get_changed_file_paths(repo, hook_name, hooks_args)
    perform_paper_trail.py         # perform_paper_trail(repo, state_file, hook_name, hooks_args)
  ver_grep/                       # version grepping
    ver_grep.py                   # grep_version(repo, state_file, ref): grep at a git ref
    branch_version.py             # grep_source_branch_version/grep_target_branch_version
    version_bump.py               # decide_version_update_type
docs/
  ttg_doc.md                      # TTG tiers & per-merge gating
  pt_doc.md                       # Paper Trail entries, glob matching, per-stage sequence
  cbm_doc.md                      # CBM concepts + PCH headers + ver_grep API
  chain_doc.md                    # Mermaid diagrams: Regular Commit/Merge/Rewrite/Patch
                                  # Apply Chains, plus one per Standalone Hook
  stub_doc.md                     # hook stub auto-determination + `hupy init`/
                                  # `hupy verify` stub management
                                  # (config field docs live in hupy/assets/.hupy.config.jsonc)
examples/
  hooks/                          # bash demos driving the real `hupy hook <stage>` CLI:
                                  # pre-commit, prepare-commit-msg, post-commit, all-hooks
                                  # (each preps its repo via tests/fixtures/prep_repo.py)
  chain/                          # bash demos driving a full Chain's stages in order, once,
                                  # against a single fixture repo: commit-chain-demo.sh,
                                  # merge-chain-demo.sh, rebase-chain-demo.sh,
                                  # patch-apply-chain-demo.sh; any -v/-q flags are forwarded
                                  # once into `hupy set verbosity` rather than per stage
  cli/                            # bash demos driving `hupy init`/`hupy verify` directly:
                                  # cli-init-demo.bash (init steps, conflict, --install-hook-stubs -f)
                                  # cli-verify-demo.bash (stub drift, sync, config-load failure)
  pch/                            # __init__.py helpers + 16 demo scripts (7 vr-* Version Release)
  ttg/                            # __init__.py helpers + 6 demo scripts
  bdc/                            # __init__.py helpers + 3 demo scripts
tests/
  conftest.py                     # root `repo_dir` fixture (tmp_path / "repo")
  fixtures/                       # cross-suite fixtures (not package-specific)
    default_repo.bundle           # minimal git bundle
    prep_repo.py                  # scenario repo generator (CLI + importable); writes .hupy.config.jsonc
    config_fixture.py             # load_config_fixture(overrides): deep-merge onto shipped asset
  cbm/ vg/ cli/ config_file/ state/ should_run_module/ stub/ pch/ ttg/ bdc/  # per-module suites
.hupy.config.jsonc                # this repo dogfoods hupy on itself
pyproject.toml
```

### Testing Infrastructure

- **Fixtures** — the root `tests/conftest.py` defines `repo_dir` (under `tmp_path`, auto-cleaned) and is the only place that `sys.path.insert(tests/fixtures)`s, so every suite can reach `prep_repo`/`config_fixture` without repeating the shim. Each suite's own `conftest.py` builds on `repo_dir` for whatever that suite needs prepared the same way every test: `cli/conftest.py`'s `git_repo_dir`/`stub_names`, `pch/conftest.py`'s `feature_landing_repo`/`version_release_repo`, `vg/conftest.py`'s `make_merge_repo_with_version` (factory)/`merge_repo_without_version_file`, `config_file/conftest.py`'s `shipped_config`, `cbm/grct/conftest.py`'s `repo`. `tests/fixtures/config_fixture.py`'s `load_config_fixture(overrides)` builds a validated `HupyConfigFile` by deep-merging `overrides` onto the shipped default asset — the standard way to build config now that the schema carries no defaults.
- **Repo scenarios** — `tests/fixtures/prep_repo.py` clones `default_repo.bundle` and constructs branches/commits/merge state. Three builders: `prepare_repo(dest, scenario)` for the TTG/PCH `SCENARIOS` unit tests exercise; `prepare_repo_with_files(dest, bucket, files)` for an arbitrary manifest against a `COMMIT_BUCKET`; `prepare_demo_repo(dest, bucket)` for demo-only `DEMO_BUCKETS` (six merge types with no `tests/pch/` assertions yet) plus seven `release_*` buckets backing the `vr-*` scripts. Also runnable standalone (`--scenario`/`--demo-bucket` + `--dest`); the bash demos shell out to it. `prep_repo.py`'s `_write_config_file` copies the shipped `DEFAULT_CONFIG_ASSET` onto each scenario repo as an untracked `.hupy.config.jsonc`, then overwrites `vg.version_file`/`version_line_pattern` to `"setup.cfg"`/`r"version\s*=\s*(\S+)"` so every scenario's committed `setup.cfg` version resolves; callers that build a repo by hand (eg `examples/bdc/__init__.py`'s `prepare_demo_repo_on_branch`) must call `_write_config_file` themselves, or `should_run_module`'s config lookup errors with a missing-config-file log.
- **Suite-local helpers** — a suite's `__init__.py` (making its directory a real package; test files reach it with `from . import ...`) holds plain functions a test calls explicitly, multiple times or with varying arguments, mid-test — not fixture material. `tests/pch/__init__.py` holds `COMMIT_EDITMSG` read/write/seed/inspect helpers; `tests/cli/__init__.py` holds `run_init_cli` and the `core.hooksPath` get/set helpers; `tests/cbm/grct/__init__.py` holds merge-repo builders consumed by its own `conftest.py`. There are no more `*_helpers.py` modules — anything called the same way every time became a `conftest.py` fixture instead (see Fixtures above).
- **Demo helpers** — `examples/{pch,ttg,bdc}/__init__.py` hold the `sys.path` shim onto `tests/fixtures/` plus the repo-prep + library-call wrappers shared by that directory's `*-demo.py` scripts, pulled in with `from __init__ import ...` (a run script's own directory is auto-added to `sys.path`, unlike a `tests/` suite package it isn't a real package so it can't use `from . import ...`).
- **Test file naming** — mirrors source: `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py`, dashes throughout except the literal `_test.py` suffix, split further by scenario group (e.g. `hupy/ttg/gate_tt.py` → `tests/ttg/ttg-*_test.py`, `hupy/pch/prepend_commit_header.py` → `tests/pch/pch-*_test.py`, `hupy/cbm/get_current_commit_type.py`'s three functions → `tests/cbm/grct/cbm-grct-*_test.py`) — the sole module's name is dropped from scenario files since the package prefix already identifies it. A top-level module with no package (`hupy/should_run_module.py`) gets its own directory, dropping the `<pkg>-` prefix (`should-run-module_test.py`).
- **Coverage notes** — `ttg.staged_files`/`ttg.report_tt` are covered indirectly through `ttg-*` (the git-error path via `ttg-error_test.py`, which patches `subprocess.check_output`); `create_default_config_file` is exercised through `cli-init_test.py` (asserting the written file is byte-identical to the asset), with no dedicated test file. The six newer merge types have only `examples/pch/*-demo.py` scripts, no dedicated `tests/pch/` assertions yet. Suites patch each module's own `load_hupy_config` reference (bound per call site by `from ... import`).
