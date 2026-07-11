# hupy CONTEXT

*Last updated: 2026-07-11 — added the `hupy.state` package: `HupyStateFile` pydantic schema for a new `hupy-state.json` (`logger_verbosity`, `skip_once`, resolved inside `.git/` rather than the working tree), opened/saved atomically and thread-/process-safe via `open_state_file(repo)`; `default_logger_verbosity` dropped from `HupyConfigFile` in favor of `hupy-state.json`'s `logger_verbosity`. Added a new top-level `should_run_module(repo, state_file, module_abbr)` that combines a module's config `is_disabled` flag with a one-time `skip_once` flag (`HupyStateFile.consume_skip_once`) into a single run/skip decision, now called by `bdc`/`ttg`/`pch` (each gained a `state_file` parameter) in place of their former direct `is_disabled` checks. Added a new `hupy skip-once`/`s` CLI subcommand that flags modules for exactly one upcoming skip. Renamed the config field `ver_grep` → `vg` (schema field and JSON key only — the `hupy.ver_grep` package/module name is unchanged). See `state`/`should_run_module`/`cli` in Module Details for the full design, and `CHANGELOG.md` for the complete history of prior rounds — this line now tracks only the most recent change, not a cumulative log.*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **v0.3.0 released** — `cbm` (Commit/Branch/Merge, formerly `commit_type`), `kamilog`, `cli` (including `init`), `config_file`, `pch` (Prepend Commit Header, now covering 8 merge types), `ver_grep`, the `ttg` package (Triage Tag Gating), and `bdc` (Ban Direct Commit, the planned `branch_protection` utility) are implemented; `ensure_file_edited` is not yet started.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependencies: `GitPython>=3.1`, `pydantic>=2`, `json5>=0.9`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself; `pch`'s/`ttg`'s/`bdc`'s use of `cbm`; `cbm`'s/`ver_grep`'s/`bdc`'s use of `config_file`; and `bdc`'s/`ttg`'s/`pch`'s use of the top-level `should_run_module`, which itself depends on both `config_file` and `state`.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | CLI entrypoint, argument parsing/dispatch (`cli_main.py`); `init` subcommand and Git repo loading (`cli_init.py`); `pre-commit`/`prepare-commit-msg` stage runners (`cli_pre_commit.py`, `cli_prepare_commit_msg.py`); `skip-once` one-time module-skip flagger (`cli_skip_once.py`) |
| `cbm` | **implemented** | Commit/Branch/Merge — classify a branch name as a `BranchType` and an in-progress commit as a `CommitType` enum member (formerly the flat `commit_type` module) |
| `config_file` | **implemented** | `HupyConfigFile` pydantic schema for `.hupy.config.jsonc` (including the nested `vg` and `cbm` sections), cached loading (as JSON5) resolved against an already-open `git.Repo`, and default-config-copying helpers |
| `state` | **implemented** | `HupyStateFile` pydantic schema for `hupy-state.json` (process verbosity, one-time module-skip flags), path resolution inside `repo.git_dir`, and thread-/process-safe atomic load-and-save via `open_state_file(repo)` |
| `should_run_module` | **implemented** | top-level gate combining a module's config `is_disabled` flag with its `hupy-state.json` `skip_once` flag into one run/skip decision; consumed by `bdc`/`ttg`/`pch` — `vg`/`hb` are listed as skippable (`skip-once` accepts them) but have no call site consuming the gate yet |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for all 8 `cbm` merge types; several append a version number via `ver_grep` when configured |
| `ver_grep` | **implemented** | extract a merge's source/target branch version string by regex-matching a line in a configured version file, read at that branch's git tip; also classifies major/minor/patch version bumps |
| `ttg.triage_tag_type` | **implemented** | `TriageTagType` flag enum (3 tiers × 4 kinds) |
| `ttg.comment_style` | **implemented** | map a file extension to its comment-leader token, for type-aware TT matching |
| `ttg.detect_tt` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.staged_files` | **implemented** | list staged files in a repo, filtered against `ignored_path_globs` |
| `ttg.report_tt` | **implemented** | render/log gated triage tag findings and abort the commit |
| `ttg.gate_tt` | **implemented** | gate commits by triage tag presence on protected branches |
| `bdc` | **implemented** | Ban Direct Commit — block a commit made directly on a protected branch, while still allowing that branch to receive commits through a merge |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit; a bash-era utility being ported, per the `# todo reimplement ensure file modified` marker in `hupy/__init__.py` |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **mostly stateless** — relies primarily on git state and file diffs; the one exception is `hupy-state.json` (see `state` in Module Details), a small process-local file holding transient operator intent (logger verbosity, one-time module skips) rather than repo policy — that stays in the tracked, reviewable `.hupy.config.jsonc`
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

**Decision**: `hupy init` sets a repo up with two artifacts:

1. A tracked, dot-prefixed config file at the repo root, **`.hupy.config.jsonc`** (JSON5/JSONC, comments allowed) — the config surface: which features (`ttg`, `pch`, and future ones) are enabled, and in what order they run per hook stage. Being tracked/committed, it's reviewable and shared across clones the same way any other project file is. Default content is copied verbatim from a packaged asset, `hupy/assets/.hupy.config.jsonc` (see `config_file` in Module Details), whose own comments document each field — not generated from `HupyConfigFile` defaults, since the schema no longer carries any.
2. Three thin stub scripts copied into the repo's actual hooks directory: `pre-commit`, `prepare-commit-msg`, and `post-commit`, sourced from the packaged `hupy/assets/hook-stubs/`. Each stub does nothing but invoke the corresponding CLI stage group — `"<python>" -m hupy hook pre-commit` / `"<python>" -m hupy hook prepare-commit-msg` / `"<python>" -m hupy hook post-commit` — which then reads `.hupy.config.jsonc` via `load_hupy_config(repo)`; today `vg` and `cbm` are consumed (feature enable/order fields aren't in `HupyConfigFile` yet — see `cli` and `config_file` in Module Details). Each stage also opens `hupy-state.json` via `open_state_file(repo)` for the run's verbosity baseline and one-time module skips — see `state` in Module Details; unlike the two `init`-written artifacts above, this file is not created by `init`, it's created lazily (from schema defaults) the first time any stage runs. The `post-commit` stage carries no hook bracket or config-driven feature — it exists solely to clear `skip_once` (`state_file.reset_for_next_commit()`) once the round has fully landed, since clearing it any earlier (eg in `prepare-commit-msg`) would drop skips before `commit-msg`-adjacent tooling could observe them.

- **Config surface = `.hupy.config.jsonc`, not the hook script.** This reverses an earlier "config surface = the script itself" decision (see *Prior rejections* below). The hook stub is a fixed, content-free trampoline; enabling/disabling a feature and controlling its order both become a config edit, not a bash edit.
- **Dot-prefixed naming (`.hupy.config.jsonc`, not `hupy.config.jsonc`)**: chosen by analogy to the Python ecosystem's single-purpose tool-config dotfiles (`.flake8`, `.pylintrc`, `.coveragerc`, `.isort.cfg`), and specifically to `.pre-commit-config.yaml` — the closest sibling in the ecosystem (same domain: tracked, root-level git-hook-orchestration config) and the exact framework rejected below as a dependency. Visible top-level docs in this repo (`AGENTS.md`, `CHANGELOG.md`, `CONTEXT.md`) were considered as a naming precedent and rejected — those are human-authored prose meant to be read, not tool-consumed config. The `.jsonc` extension (renamed from `.json`) reflects the file now being parsed as JSON5 rather than strict JSON, so it can carry the `//` comments documenting each field.
- **Hooks directory is resolved, not fixed to `.git/hooks/`.** `hupy.cli.cli_init._resolve_hooks_dir(repo)` reads `core.hooksPath` via GitPython's `config_reader()` and joins it onto `repo.working_tree_dir` if set (resolving relative to the repo root; an absolute configured path is used as-is since `pathlib` path-joining drops the left side when the right side is absolute), otherwise falls back to `pathlib.Path(repo.git_dir) / "hooks"`. `--hooks-dir` overrides this resolution entirely. `init` itself never writes `core.hooksPath` — an earlier design's redirection-at-a-tracked-directory approach (see *Prior rejections*) is unnecessary now that the hook scripts carry no meaningful content of their own; the reviewable content lives in `.hupy.config.jsonc` instead.
- **Per-file conflict checks, not directory-level.** `_copy_hook_stubs` only checks whether each individual target filename (`pre-commit`, `prepare-commit-msg`) already exists — not whether the hooks directory itself exists. `.git/hooks/` always exists after `git init` (populated with git's own `*.sample` files), so a directory-existence check would force `-f` on every default-path run; per-file checks let a fresh repo's first `init` succeed without `-f` while still protecting a real pre-existing hook.
- **Calls the CLI, not internal functions.** The stub invokes `<python> -m hupy <subcommand>` rather than importing `hupy.ttg`/`hupy.pch` Python functions directly, because the CLI subcommands are `hupy`'s stable, documented public interface.
- **Interpreter path is baked in at install time, not resolved from `PATH`.** The packaged stub templates carry a `"{{PYTHON}}"` placeholder; `_copy_hook_stubs` substitutes it with `sys.executable` (the interpreter running `hupy init`) before writing each stub. A bare `python`/`python3` on `PATH` is unreliable for a git hook: hooks run in whatever environment invokes `git commit` — an IDE's built-in git integration, for instance, does not source the project's venv onto `PATH` — so a bare interpreter name can resolve to a system Python lacking both `hupy` and its dependencies (`ModuleNotFoundError: No module named 'git'`). Baking in the absolute path makes the hook work regardless of which client or shell state triggers the commit. A consequence: re-running `hupy init --force` is required after moving/recreating the virtualenv the package is installed in, since the old absolute path would otherwise go stale.
- **`-f`/`--force` gates the hook stubs and the config file independently** — `_copy_hook_stubs` and `create_default_config_file` each perform their own existence/`force` check, so (e.g.) a pre-existing config with fresh hooks still aborts on the config step even though the hooks were already written; `init` is not atomic across the two artifacts (mirrors the non-atomicity of the prior design between copying scripts and configuring `core.hooksPath`).
- **Enforcement caveat**: none of the above is enforceable, only convenient. Git hooks are client-side and opt-in (`git commit --no-verify` bypasses them entirely, and a developer can simply never run `hupy init`). Guaranteed enforcement, if ever needed, requires a server-side mechanism (CI required-checks, branch protection, or a self-hosted server's `pre-receive` hook), independent of this model.

#### Prior rejections

Kept for their still-relevant reasoning, though the decisions above have since reversed or replaced them:

An earlier design wired `hupy` into git with a plain bash script per hook stage, tracked in the consuming repo at `scripts/hupy-hooks/<hook-name>`, calling the CLI directly in sequence, with `git config core.hooksPath scripts/hupy-hooks` pointing git at that tracked directory (`git config core.hooksPath` looks for a file named exactly after the hook type in the target directory — why the CLI's `pre-commit`/`prepare-commit-msg` subcommand groups are named after the git hook stages, which is unchanged). Feature enable/disable was a comment-toggle on the CLI-call line inside that tracked script, and execution order was simply the line order. Symlinking tracked files into `.git/hooks/` was considered and rejected at the time — same one-time-setup burden as `core.hooksPath`, but fragile on Windows (requires symlink privileges/`core.symlinks`).

Rejected the `pre-commit`-framework route (pre-commit.com): it would add a hard dependency on an external hook manager (install, `.pre-commit-config.yaml`, `rev:` pinning) on top of `hupy` itself, plus its own packaging burden (`.pre-commit-hooks.yaml`, `language: python` entry points, `pass_filenames: false` on every hook since neither `ttg` nor `pch` accept positional file args, and a second `pre-commit install --hook-type prepare-commit-msg` for `pch` specifically since it needs that stage) — at odds with the *composable*/*simple defaults* principles above and with `hupy`'s bash-script origin. Wrapping `hupy` as a `.pre-commit-hooks.yaml` hook is technically easy and may be revisited later as an optional secondary path, but is not planned work.

Previously rejected a declarative config file (`.hupy.toml` or similar): the reasoning at the time was that it would require a config-loading module (parsing, validation, defaults-merging) that didn't exist, and that TOML tables have no inherent execution order (would need an explicit `sequence = [...]` key to recover what the bash script's line order gave for free). That rejection is reversed by the current design, which adopts `.hupy.config.json` as the config surface — the intent is for execution order to be expressed explicitly in JSON (e.g. an array per stage) rather than relied upon implicitly, though the schema itself isn't implemented yet (see `setup` in Module Details).

`examples/{pch,ttg}/*.py` remain demo/test scripts (see Testing Infrastructure) run standalone for scenario walkthroughs — they are not, and were never meant to be, install-ready hook scripts, and this is unaffected by the redesign.

## Module Details

### `cbm`

Commit/Branch/Merge — classifies branch names and in-progress commits from git state (formerly the flat `commit_type` module).

**Public API**: `BranchType`, `CommitType`, `get_current_commit_type(repo)`, `get_source_branch(repo)`, `get_target_branch(repo)` (`hupy/cbm/__init__.py`); all take an already-open `git.Repo`, not a path.

**`BranchType(Enum)`** — `FEATURE` | `DEV` | `MAIN` | `HOTFIX` | `RELEASE` | `USER`. `BranchType.from_name(branch_name, repo)` classifies against the `cbm` section of `.hupy.config.jsonc` (via `load_hupy_config(repo).cbm`), checked in order: `dev_branch_name` → `DEV`, `main_branch_name` → `MAIN`, `f"{hotfix_branch_prefix}/"` prefix → `HOTFIX`, `f"{release_branch_prefix}/"` prefix → `RELEASE`, any other `/` in the name → `USER`, otherwise → `FEATURE`. Branch names are no longer hardcoded (previously module-level `MAIN_BRANCH = "main"`/`DEV_BRANCH = "dev"` constants).

**`CommitType(Flag)`** — two-level bitmask hierarchy:

- level 1: `MERGE` | `OTHER_COMMIT`
- level 2 (under `MERGE`): `FEATURE_LANDING` | `VERSION_RELEASE` | `SYNC_BACKPORT` | `CATCH_UP` | `HOTFIX_RELEASE` | `HOTFIX_BACKPORT` | `RELEASE_CUT` | `RELEASE_BACKPORT` | `OTHER_MERGE`

`CommitType.decide_commit_type(source, target)` maps a `(BranchType, BranchType)` pair via `_MERGE_TYPE_BY_BRANCH_PAIR`: `(FEATURE, DEV)`→`FEATURE_LANDING`, `(DEV, MAIN)`→`VERSION_RELEASE`, `(MAIN, DEV)`→`SYNC_BACKPORT`, `(DEV, FEATURE)`→`CATCH_UP`, `(HOTFIX, MAIN)`→`HOTFIX_RELEASE`, `(HOTFIX, DEV)`→`HOTFIX_BACKPORT`, `(RELEASE, MAIN)`→`RELEASE_CUT`, `(RELEASE, DEV)`→`RELEASE_BACKPORT`; any other pair → `OTHER_MERGE`. See `docs/cbm_doc.md` for the full Branch/Merge Type concept tables and Mermaid graphs.

`get_current_commit_type(repo)` classification logic (in order):

1. no `MERGE_HEAD` → `OTHER_COMMIT`
2. `MERGE_HEAD` has multiple lines (octopus merge) → `OTHER_MERGE`
3. `MERGE_HEAD` SHA matches any remote tracking ref of the target branch (pull merge) → `OTHER_MERGE`
4. otherwise resolve `BranchType.from_name` for source and target branches and call `CommitType.decide_commit_type`

`CHERRY_PICK_HEAD` and `REVERT_HEAD` detection is present in git but the corresponding `CommitType` members are not yet defined.

`_is_pull_merge(repo, sha, target_branch)` returns `False` early if `target_branch` is `None` (detached HEAD) to avoid `TypeError` when accessing `remote.refs[None]`. `get_target_branch(repo)` returns `None` on detached HEAD.

`get_source_branch`/`get_target_branch`/`get_current_commit_type` each cache their result per `repo.git_dir` in module-level dicts, so repeated calls against the same `git.Repo` (e.g. from both `pch` and `ttg` dispatch) hit git only once.

Repo construction/error handling (`git.InvalidGitRepositoryError`/`NoSuchPathError`) is the caller's responsibility — these functions take a `git.Repo`, they don't build one.

Not yet exposed as its own CLI subcommand (`# todo consider expose commit type as part of cli`) — currently only consumed internally by `pch` and `ttg`.

### `pch`

Prepend Commit Header — rewrites in-progress commit messages to prepend informational headers for merge commits.

**Public API**: `prepend_commit_header(repo, state_file)` — returns immediately if `should_run_module(repo, state_file, "pch")` is `False` (config-disabled or one-time-skipped; see `should_run_module` in Module Details), before `logger.enter(...)` or any commit-type detection; otherwise detects current commit type via `cbm.get_current_commit_type(repo)`, then prepends an appropriate header and rewrites `.git/COMMIT_EDITMSG`

Header generation logic — a `_HEADER_GENERATORS` dict keyed by `CommitType`, one generator per merge type:

| `CommitType` | Header format |
|---|---|
| `FEATURE_LANDING` | `"Feature Landing: <source-branch-name>"` (via `get_source_branch(repo)`) |
| `VERSION_RELEASE` | `"<bump><release-type>: <version>"`, eg `"Minor Prototype Release: 0.4.0"`, `"Alpha Release: 1.3.0-alpha.1"`, `"Release Candidate: 1.3.0-rc.1"` — see release-type/bump breakdown below; falls back to `"Version Release: <version>"` when the version doesn't parse as a `major.minor.patch` core, or plain `"Version Release"` with no source version at all |
| `SYNC_BACKPORT` | `"Sync Backport from: <version>"` or plain `"Sync Backport"` |
| `CATCH_UP` | `"Catch Up: <target-branch-name>"` (via `get_target_branch(repo)`) |
| `HOTFIX_RELEASE` | `"<bump>Hotfix Release: <version>"` or plain `"Hotfix Release"` |
| `HOTFIX_BACKPORT` | `"Hotfix Backport from: <version>"` or plain `"Hotfix Backport"` |
| `RELEASE_CUT` | `"<bump>Release Cut: <version>"` or plain `"Release Cut"` |
| `RELEASE_BACKPORT` | `"Release Backport from: <version>"` or plain `"Release Backport"` |

`<bump>` above (`_get_version_bump_prefix`, from `ver_grep.decide_version_update_type`) is `"Major "`/`"Minor "`/`"Patch "`/`""`, comparing source vs target version; empty when no bump is detected or a version doesn't resolve.

`VERSION_RELEASE`'s `<release-type>` comes from `_get_release_type_word(version, pch_config)` (`pch_config = load_hupy_config(repo).pch`), checked in this order: `pch_config.alpha_tag`/`beta_tag`/`release_candidate_tag` as a substring of `version` → `"Alpha Release "`/`"Beta Release "`/`"Release Candidate "` (each check skipped if its tag is empty — RC's word already reads "Release Candidate", so it doesn't also get a trailing "Release"); else `enable_pre_alpha` and a `0.9.z` core → `"Pre-Alpha Release "`; else `enable_vertical_slice` and a `0.5.z`-`0.9.z` core → `"Vertical Slice Release "`; else any other `0.x.z` core → `"Prototype Release "`; else `>=1.0.0` → `"Stable Release "`; else `""` (unparsable, triggers the plain fallback above). `<bump>` is forced to `""` for the Alpha/Beta/Release Candidate release types even when a bump would otherwise be detected.

`OTHER_COMMIT`/`OTHER_MERGE` (not in `_HEADER_GENERATORS`) → file left untouched, no exception.

The rewrite separates comment lines (starting with `#`) from content, placing all comments after the content block to preserve git's template comments. Non-destructive on failure: if the atomic write via `os.replace()` fails, the original file is untouched and the temporary file is cleaned up.

**Known gap**: `examples/pch/hotfix-backport-demo.py`'s docstring/expected output still says "skip (merge type not yet handled by PCH)", left over from before `HOTFIX_BACKPORT` gained a generator above — it's stale relative to the current code and should be updated to expect a header.

README flags a planned scenario not yet covered by `examples/pch/`/`tests/pch/`: keeping a feature branch up to date by merging `dev` back *into* it (as opposed to the Feature Landing direction, feature → `dev`) — this is now `CATCH_UP` above and has a demo/bucket, but no dedicated `tests/pch/` assertions yet.

### `config_file`

Config schema, loading, and default-copying for `.hupy.config.jsonc`.

**Public API**: `CONFIG_LOGGER_NAME` (`hupy/config_file/__init__.py`, `= "HU.config-file"`) · `HupyConfigFile` (`config_file.py`, renamed from `hupy_config_file.py`/`HupyConfig`/`model.py`) · `CONFIG_FILENAME`, `DEFAULT_CONFIG_ASSET`, `get_config_file_path(repo)` (`config_file_path.py`) · `load_hupy_config(repo)` (`load_config.py`) · `create_default_config_file(repo, force)` (`write_config.py`, renamed from `write_default_config(repo_root, force)`)

- **`HupyConfigFile(BaseModel)`** — `hupy_version: str`, `vg: _VerGrep`, `ttg: _Ttg`, `cbm: _Cbm`, `pch: _Pch`, `bdc: _Bdc`, and `hb: _Hb`. The former `default_logger_verbosity: int` field (base verbosity for `-v`/`-q` offsets) has since been removed and replaced by `hupy-state.json`'s `logger_verbosity` (see `state` in Module Details) — process behavior, not per-repo policy, matching the `# Fixme mv to state file` marker that used to sit on this field. **None of the remaining fields, nor any nested `_VerGrep`/`_Ttg`/`_Cbm`/`_Pch`/`_Bdc`/`_Hb` field, carry a Python-side default any more** — every value must come from the config file on disk. The single source of default values is now the shipped asset `hupy/assets/.hupy.config.jsonc` (see `create_default_config_file` below), not the pydantic schema; `tests/fixtures/config_fixture.py`'s `load_config_fixture(overrides)` fills this gap for tests by deep-merging onto that same shipped asset rather than constructing `HupyConfigFile` from partial kwargs
- A `model_validator(mode="after")` on `HupyConfigFile` compares `hupy_version` against `importlib.metadata.version("HUPy")` and `logger.warning(...)`s (via `CONFIG_LOGGER_NAME`) on a mismatch, without raising — catches a config file left over from an older `hupy` install after the package itself is upgraded
- **per-module `is_disabled: bool`** — `_VerGrep`, `_Ttg`, `_Pch`, and `_Bdc` each carry this field (`_Hb` already had it before this round, unconsumed since `hb` has no implementation yet). `ttg`/`pch`/`bdc` now check it via the shared top-level `should_run_module(repo, state_file, module_abbr)` gate (see `should_run_module` in Module Details) rather than each checking `config.<mod>.is_disabled` directly; `_VerGrep` is the one exception — its own `model_validator` still reads `is_disabled` directly, at config-validation time, purely to suppress the unconfigured-field warning (see `_VerGrep(BaseModel)` below), not to gate whether `ver_grep`'s functions run
- **`_VerGrep(BaseModel)`** — `is_disabled: bool`, `version_file: pathlib.Path`, `version_line_pattern: str`, exposed on `HupyConfigFile` as the **`vg`** field (see `ver_grep` in Module Details for how these are consumed). `is_unconfigured()` returns `True` when `version_file` is empty/`"."` (`pathlib.Path("")` normalizes to `.`) or `version_line_pattern` is blank. A `model_validator(mode="after")` returns immediately when `is_disabled` is `True` (before the unconfigured check, so a disabled `vg` never logs the unconfigured warning either); otherwise calls `is_unconfigured()` and, if `True`, logs a `logger.warning(...)` via `CONFIG_LOGGER_NAME` rather than raising — an unconfigured (but not disabled) `vg` is a valid, non-fatal state (e.g. the shipped default config's empty `version_file`/`version_line_pattern`)
- **`_Ttg(BaseModel)`** — `is_disabled: bool`, `disable_tt_detect_by_type: bool`, `ignored_path_globs: list[str]`; all three now consumed by `ttg.gate_tt`: `is_disabled` by `perform_triage_tags_gating`, `disable_tt_detect_by_type`/`ignored_path_globs` by `_perform_triage_tags_by_filtering_group` (see `ttg.gate_tt`/`ttg.detect_tt`/`ttg.staged_files` in Module Details)
- **`_Cbm(BaseModel)`** — `main_branch_name: str`, `dev_branch_name: str`, `hotfix_branch_prefix: str`, `release_branch_prefix: str` (all `Field(min_length=1)`); consumed by `cbm.branch_type.BranchType.from_name` (see `cbm` in Module Details)
- **`_Pch(BaseModel)`** — `is_disabled: bool`, `enable_vertical_slice: bool`, `enable_pre_alpha: bool`, `alpha_tag: str`, `beta_tag: str`, `release_candidate_tag: str` (the tag fields are plain strs, no `min_length` — empty disables that tag's recognition); consumed by `pch.prepend_commit_header` (`is_disabled` at the top of `prepend_commit_header`, the rest by `_get_release_type_word` — see `pch` in Module Details)
- **`_Bdc(BaseModel)`** — `is_disabled: bool`, `ban_commit_to_main: bool`, `ban_commit_to_dev: bool`, `ban_commit_to_branches: list[str]`; consumed by `bdc.ban_direct_commit` via the shared `should_run_module` gate (see `bdc`/`should_run_module` in Module Details) — the previous known gap where the disabled check read the wrong config field is resolved by that gate's generic `getattr(config, module_abbr).is_disabled` lookup
- **`load_hupy_config(repo)`** — takes an already-open `git.Repo`, not a path (resolving the repo is the caller's job, e.g. via `hupy.cli.cli_init.load_git_repo(repo_path)`). Reads `get_config_file_path(repo)` (`config_file_path.py`: `pathlib.Path(repo.working_tree_dir) / CONFIG_FILENAME`), parses it with `json5.loads()` (comments/trailing commas tolerated), then `HupyConfigFile.model_validate()`-validates the resulting dict; on `FileNotFoundError` or `pydantic.ValidationError`, logs and `raise SystemExit(1) from e` rather than propagating the exception. Caches the validated instance in a module-level `_config_cache` so the file is read from disk only once per process — repeated calls (e.g. from `cli_pre_commit`/`cli_prepare_commit_msg`/`cli_verify` dispatch, `cbm.branch_type`, `ver_grep.branch_version`, and `should_run_module`) return the same instance
- **`create_default_config_file(repo, force)`** — same existence/`force` conflict pattern as `_copy_hook_stubs` (see `cli` below), but now `shutil.copyfile`s the packaged asset `hupy/assets/.hupy.config.jsonc` (path in `config_file_path.DEFAULT_CONFIG_ASSET`) to `get_config_file_path(repo)` verbatim, rather than serializing `HupyConfigFile()` defaults — the asset's own `//` comments are the field documentation (replacing the deleted `docs/hupy_config_doc.md`; `# Fixme rework .jsonc comments, along w/ complete doc rewrite` marks that pass as still pending). Used by `hupy init`, not by `load_hupy_config`
- **`verify-config-file`** CLI subcommand (`cli_verify.py`, see `cli` below) just calls `load_hupy_config(repo)` and reports success/failure — no separate validation function of its own
- `tests/config_file/config-shipped_config_file_test.py` asserts the shipped asset both validates against `HupyConfigFile` and has `hupy_version` matching the installed package version — guards against the asset drifting from the schema or going stale across a version bump; `write_default_config`/`create_default_config_file` itself has no dedicated test file (still exercised indirectly through `tests/cli/cli-cli_init_init_cli_test.py`; `# todo unit test for configs` in `hupy/config_file/__init__.py`)

### `state`

Local, untracked process state for `hupy-state.json` — the one deliberate exception to the *mostly stateless* design principle above (see Design Principles). Mirrors `config_file`'s shape (schema module + path-resolver module) but resolves inside the repo's `.git` directory rather than its working tree, since this file is never meant to be committed or shared across clones.

**Public API**: `STATE_LOGGER_NAME` (`hupy/state/__init__.py`) · `HupyStateFile` (`state_file.py`) · `STATE_FILENAME`, `get_state_file_path(repo)` (`state_file_path.py`) · `open_state_file(repo)` (`open_state.py`)

**Known gap**: `STATE_LOGGER_NAME = PROJ_LOGGER_NAME + "state"` is missing the `.` separator every other `*_LOGGER_NAME` constant uses (`CONFIG_LOGGER_NAME = PROJ_LOGGER_NAME + ".config"`, `TTG_LOGGER_NAME = "HU.TTG"`, etc.), so it resolves to `"HUstate"` rather than the expected `"HU.state"` — functionally harmless (still a valid, distinct logger name) but inconsistent with the rest of the codebase's logger-naming convention.

- **`HupyStateFile(BaseModel)`** — `logger_verbosity: int = 1`, `skip_once: set[str] = Field(default_factory=set)`. Unlike `HupyConfigFile`'s fields, these two carry real Python-side defaults, since there is no shipped default asset for this file — a missing `hupy-state.json` is a normal first-run state, not an error
- **`HupyStateFile.consume_skip_once(module_abbr)`** — checks `module_abbr` against `skip_once` and returns whether it was found, without discarding it; called by `should_run_module` (see below), so a flag set by `skip-once` stays set across every check within a round (eg `hb`'s lead/trail brackets, checked across both the `pre-commit` and `prepare-commit-msg` hook stages)
- **`HupyStateFile.clear_skip_once()`** — empties `skip_once` in one call; `cli_prepare_commit_msg._prepare_commit_msg_main` calls it right after `prepare-commit-msg`'s trailing hook bracket, so the whole set is spent exactly once, at the end of the round (`prepare-commit-msg` is the last of the two hook stages to run) rather than on each individual `consume_skip_once` check
- **`STATE_FILENAME`** (`= "hupy-state.json"`) · **`get_state_file_path(repo)`** — `pathlib.Path(repo.git_dir) / STATE_FILENAME`, i.e. inside `.git/`, not the working-tree root like `get_config_file_path` — this is what keeps the state file untracked and per-clone rather than shared
- **`open_state_file(repo)`** — a `@contextlib.contextmanager` that makes reading and writing `hupy-state.json` thread- and process-safe: acquires an in-process `threading.Lock` **and** an `fcntl.flock`'d `.lock` sibling file (so two separate `hupy` processes racing on the same repo, not just two threads in one process, serialize correctly), reads the existing file via `HupyStateFile.model_construct(**json.loads(...))` (no validation — deliberately permissive of a hand-edited or slightly-stale file) if it exists, else yields fresh `HupyStateFile()` defaults; after the caller's `with` block finishes, writes the (possibly-mutated) state back via `tempfile.mkstemp` + `os.fdopen`/`model_dump_json(indent=2)` + `os.replace` (atomic rename, so a crash mid-write never leaves a corrupt file), cleaning up the tempfile if the write itself fails; the file lock is released in a `finally` regardless of outcome. Callers (`cli_pre_commit`, `cli_prepare_commit_msg`, `cli_skip_once`) hold this context open for their entire dispatch body, so every state read/mutation across a single hook invocation shares one open+save cycle
- No dedicated CLI subcommand initializes `hupy-state.json` the way `init --create-config-file` does for `.hupy.config.jsonc` — it's created lazily, from schema defaults, by whichever of `pre-commit`/`prepare-commit-msg`/`skip-once` runs first

### `should_run_module`

Top-level module (`hupy/should_run_module.py`), not nested in any package — same tier as `kamilog.py`. Centralizes the run/skip decision that `bdc`, `ttg`, and `pch` each used to make on their own by checking `config.<mod>.is_disabled` directly.

**Public API**: `should_run_module(repo, state_file, module_abbr)` — checks two independent skip sources and returns `True` only if neither fires:

1. `getattr(config, module_abbr).is_disabled` (loaded via `load_hupy_config(repo)`) — checked first, since it's a cheap in-memory read (config is cached) and requires no `state_file` I/O
2. `state_file.consume_skip_once(module_abbr)` — only reached if step 1 didn't already return `False`; this ordering means a config-disabled module never consumes a pending `skip_once` flag — the flag stays queued for a future round where the module is actually enabled

Both branches log via `logger.skip(...)` (shared `PROJ_LOGGER_NAME` logger, not a dedicated `*_LOGGER_NAME`) using a display name resolved from a local `_MODULE_ABBR_TO_NAME` dict (`"vg"`→`"VerGrep"`, `"ttg"`→`"Triage Tag Gating"`, `"pch"`→`"Prepend Commit Header"`, `"bdc"`→`"Ban Direct Commit"`, `"hb"`→`"Hook Bracket"`) — Title Case, distinct from `cli_skip_once.py`'s own kebab-case full-name mapping used for CLI argument matching (see `cli` in Module Details); the two mappings currently duplicate the same five abbrs rather than sharing one source.

**Known gap**: only `bdc`, `ttg`, `pch`, and `hb` (via `perform_hook_brackets`) actually call `should_run_module`. `vg` is listed in `cli_skip_once.SKIPPABLE_MODULE` and has an entry in this module's own `_MODULE_ABBR_TO_NAME`, so `hupy skip-once vg` succeeds and writes to `skip_once` without error — but nothing ever calls `should_run_module(repo, state_file, "vg")` to consult that flag, so flagging it is currently a silent no-op. `vg` (`ver_grep`) has no standalone CLI entry point of its own to gate — it's only ever invoked internally by `pch`.

### `ver_grep`

Reads a merge's source/target branch version string by regex-matching a line in a configured version file, resolved at that branch's git tip (not the working tree — mid-merge, the working tree only ever holds the target branch's, possibly conflicted, content); consumed by `pch` to append version numbers to several merge-type commit headers. Formerly a flat module exposing a single `grep_repo_version()`, now a package split by branch role, plus a version-bump classifier.

**Public API** (`hupy/ver_grep/__init__.py`): `grep_source_branch_version()` · `grep_target_branch_version()` · `decide_version_update_type(source_version, target_version)`

- **`grep_source_branch_version()` / `grep_target_branch_version()`** (`branch_version.py`) — both take no arguments; each resolves `repo = git.Repo(os.getcwd(), search_parent_directories=True)`, loads the `vg` config section via `load_hupy_config(repo)`, resolves the relevant branch name via `cbm.get_source_branch(repo)`/`get_target_branch(repo)`, then reads that branch's version file at its tip via `repo.git.show(f"{ref}:{version_file}")` and `re.search(pattern, line)`s each line in order, returning the first capturing-group match. Note: `is_disabled` is checked inside `_VerGrep`'s own `model_validator` (see `config_file` in Module Details), not here, and these functions are not wired through `should_run_module` (see `should_run_module` in Module Details) — they have no run/skip gate of their own beyond `is_unconfigured()`. Flow, in order:
  1. if `config.vg.is_unconfigured()` → `logger.warning(...)` and return `""` — a non-fatal, expected state, not an error
  2. if `version_file` doesn't exist at that branch's tip → `logger.error(...)` + `raise SystemExit(1)`
  3. no line matches the pattern → `logger.error(...)` + `raise SystemExit(1)`
- **`decide_version_update_type(source_version, target_version)`** (`version_bump.py`) — parses `major.minor.patch` cores via `^(\d+)\.(\d+)\.(\d+)` (ignoring any pre-release/build suffix), returns `"x"` for a major bump, `"y"` for minor, `"z"` for patch, or `""` if unparsable or not actually a bump (equal or lower) — **not yet wired into `pch`**, available for future use (e.g. picking a header word by bump size)
- Own logger `VER_GREP_LOGGER_NAME` (`"HU.VerGrep"`), propagation disabled.

### `ttg.triage_tag_type`

**`TriageTagType(Flag)`** — 12 members across 3 tiers × 4 kinds (`TODO`/`FIXME`/`HACK`/`BUG`), each matched case-sensitively (`TODO` loud, `Todo` steady, `todo` quiet); composite groups `LOUDS`/`STEADYS`/`QUIETS` (by tier) and `TODOS`/`FIXMES`/`HACKS`/`BUGS` (by kind) are pre-defined flag combinations. Purely the enum definition — no line-scanning or filtering methods live here any more; group membership is checked directly via `Flag`'s native `in` operator (eg `tag in TriageTagType.LOUDS`) rather than a dedicated classmethod.

### `ttg.comment_style`

Maps a file's extension to the comment-leader token expected for that language.

**Public API**: `get_comment_prefix_for_file(file_path)` → `str | None` — looks up `pathlib.Path(file_path).suffix.lower()` against a fixed dict (`//` C-style: `.c`/`.cpp`/`.java`/`.js`/`.ts`/`.go`/`.rs`/…; `#` hash-style: `.py`/`.sh`/`.rb`/`.yaml`/…; `<!--` HTML-style: `.html`/`.xml`/`.md`/…); returns `None` for an unmapped or missing extension, in which case `detect_tt` falls back to matching a TT tag anywhere in the line.

### `ttg.detect_tt`

Scans staged git diffs for triage tag annotation markers.

**Public API**: `detect_triage_tags_in_staged_file(file_path, repo_root=None, disable_tt_detect_by_type=False)` → `list[(TriageTagType, str, int)]` — runs `git diff --cached -- file_path`, tracks the current line number from each hunk header, and for every added (`+`) line records the first matching tag, the line text, and its line number via the module-private `_find_first_tag_in_line(line, comment_prefix)`. `comment_prefix` is `None` when `disable_tt_detect_by_type` is `True` (match anywhere in the line); otherwise it's `comment_style.get_comment_prefix_for_file(file_path)`, and when non-`None` only a tag occurring after that comment-leader token counts as a match.

`_TT_PATTERN` (the tag-matching regex) and `_find_first_tag_in_line` live here rather than in `triage_tag_type.py`, since this is their only caller; `ttg.report_tt` imports `_TT_PATTERN` back from here to re-match the tag for highlighting when rendering a gated finding.

### `ttg.staged_files`

Lists a repo's staged files and filters them against configured ignore globs.

**Public API**: `get_staged_file_paths(repo)` — runs `git diff --cached --name-only`, `raise SystemExit(1)` on a `subprocess.CalledProcessError`; `is_path_ignored(file_path, ignored_path_globs)` — `fnmatch.fnmatch`es `file_path` against each glob.

### `ttg.report_tt`

Renders and logs gated triage tag findings, then aborts the commit.

**Public API**: `report_gated_tags(filtered_results)` — takes the `file_path -> [(tag, line, line_no)]` mapping built by `gate_tt`, logs `logger.fail(...)`, renders a per-file comment banner (`kamilog.gen_comment_banner_centered`, `"-"` fill) with each gated line, highlighting the matched tag via `AnsiRenderer.color_triage_tag` (re-matching with `detect_tt._TT_PATTERN`), then `raise SystemExit(1)`.

### `ttg.gate_tt`

Triage tag (TT) gating — blocks commits that introduce annotation markers on protected branches.

**Public API**: `perform_triage_tags_gating(repo, state_file)` — returns immediately if `should_run_module(repo, state_file, "ttg")` is `False` (config-disabled or one-time-skipped; see `should_run_module` in Module Details), before `logger.enter(...)` or any commit-type detection; otherwise detects current commit type via `cbm.get_current_commit_type(repo)` and gates on the tag tiers appropriate to that merge type

Gating policy by commit type:

- `FEATURE_LANDING` → gates `LOUDS`
- `VERSION_RELEASE` → gates `LOUDS | STEADYS`
- anything else → skipped, no gating

`_perform_triage_tags_by_filtering_group(repo, filtering_tt_group)` loads `config.ttg` itself, rather than receiving already-loaded values as parameters (`load_hupy_config` is cached, so a second call is cheap), then orchestrates three steps, each its own helper: `staged_files.get_staged_file_paths(repo)` to list staged files; `_collect_gated_tags(...)`, which loops those files, skips ones matching `staged_files.is_path_ignored(...)`, calls `detect_tt.detect_triage_tags_in_staged_file(...)`, and filters the result by `tag in filtering_tt_group`; and, only when gated tags were found, `report_tt.report_gated_tags(filtered_results)`.

`gate_tt`, `detect_tt`, `staged_files`, and `report_tt` share one logger, `TTG_LOGGER_NAME` (`"HU.TTG"`), defined in `hupy/ttg/__init__.py` **before** the `from .gate_tt import ...` line — each module imports `TTG_LOGGER_NAME` back from the package `__init__`, so the definition must precede the import or it fails with a circular-import `ImportError`. `cbm` keeps its own separate logger, `CBM_LOGGER_NAME` (`"HU.CBM"`).

### `bdc`

Ban Direct Commit — blocks a commit made directly on a protected branch (`main` by default; `ban_commit_to_dev` defaults `False`), while still allowing that branch to receive commits through a merge (eg. `feature → dev`, `dev → main`); only the direct-commit path is blocked, merging is unaffected. Implements the previously-planned `branch_protection` utility (see Status line above).

**Public API**: `ban_direct_commit(repo, state_file)` (`hupy/bdc/ban_direct_commit.py`, re-exported from `hupy/bdc/__init__.py`) — wired into `cli.cli_pre_commit` ahead of `perform_triage_tags_gating`.

Flow, in order:

1. returns immediately if `should_run_module(repo, state_file, "bdc")` is `False` (config-disabled or one-time-skipped; see `should_run_module` in Module Details), before `logger.enter(...)`; otherwise `current_branch = get_target_branch(repo)` (`cbm`)
3. build `protected_branches` from `.hupy.config.jsonc`'s `bdc`/`cbm` sections: `config.bdc.ban_commit_to_branches` plus `config.cbm.dev_branch_name` (if `config.bdc.ban_commit_to_dev`) and `config.cbm.main_branch_name` (if `config.bdc.ban_commit_to_main`) — `_get_protected_branches(repo)`
4. `current_branch not in protected_branches` → `logger.skip(...)`, return (covers detached HEAD too, since `get_target_branch` returns `None` there)
5. `CommitType.MERGE in get_current_commit_type(repo)` → `logger.pass_(...)`, return — any merge commit into a protected branch is allowed, regardless of merge type (`FEATURE_LANDING`, `VERSION_RELEASE`, `OTHER_MERGE`, …)
6. otherwise: `logger.fail(...)` + `raise SystemExit(1)` — a non-merge commit landing directly on a protected branch

Own logger `BDC_LOGGER_NAME` (`"HU.BDC"`), propagation disabled.

### `cli`

Argument parser and entrypoint for the `hupy` command-line tool; a package (`hupy/cli/`, formerly a flat `hupy/cli.py`) split by subcommand.

**Public API**: `cli_parser` (ArgumentParser) · `cli_subparser` (subparsers action) — both in `cli_main.py` · `register_cli_init_parser`/`load_git_repo`/`INIT_LOGGER_NAME`/`REPO_PATH_HELP`/`_copy_hook_stubs`/`_resolve_hooks_dir` (`cli_init.py`) · `register_cli_hook_parser` (`hook/cli_hook.py`) · `register_cli_pre_commit_parser` (`hook/cli_pre_commit.py`) · `register_cli_prepare_commit_msg_parser` (`hook/cli_prepare_commit_msg.py`) · `register_cli_post_commit_parser` (`hook/cli_post_commit.py`) · `register_cli_verify_parser` (`cli_verify.py`) · `register_cli_skip_once_parser`/`SKIPPABLE_MODULE` (`cli_skip_once.py`)

The CLI has five top-level subcommands, mirroring the hook stages and setup; the three git hook stages nest under a `hook` subcommand group:

```
hupy init
hupy hook pre-commit
hupy hook prepare-commit-msg
hupy hook post-commit
hupy verify-config-file
hupy skip-once (alias: s)
```

- **`cli_main.py`** — main parser and dispatch, unchanged in shape from the old `cli.py`: `prog="hupy"` (a literal string, not `__package__`, since this module now lives *inside* the `hupy.cli` package and `__package__` would otherwise resolve to `"hupy.cli"`), `description=__doc__`; imports each subcommand module's `register_*_parser` and calls them in turn against `cli_subparser`
- **`init`** — implemented in `cli_init.py` (moved from the former `hupy/setup/cli_init.py`); onboards a repository onto `hupy` by writing the three hook stubs and a default `.hupy.config.jsonc`. Dispatch runs through a step registry, `_INIT_STEPS = [("copy_hooks", _run_copy_hooks), ("create_config_file", _run_create_config_file)]`, so adding a further step/flag pair is a one-line addition to the list plus one `add_argument` call. `_init_main(args)` flow:
  1. `repo = load_git_repo(args.repo_path)` — see `load_git_repo` below
  2. resolve `repo_root = pathlib.Path(repo.working_tree_dir)` — deliberately *not* the raw `args.repo_path`, so that running `hupy init` from any subdirectory still anchors `hooks_dir`/`repo_root` at the true repository root
  3. `selected_steps = [(dest, run_step) for dest, run_step in _INIT_STEPS if getattr(args, dest)]`, falling back to the full `_INIT_STEPS` list when neither `--copy-hooks` nor `--create-config-file` is passed (so plain `hupy init` still does both, unchanged from before this step registry existed)
  4. each selected step runs in registry order, passing it `args`/`repo`:
     - `_run_copy_hooks` resolves `hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)` (see Hook Integration Model for the `core.hooksPath`/`.git/hooks` fallback logic) then calls `_copy_hook_stubs(hooks_dir, args.force)` — `hooks_dir.mkdir(parents=True, exist_ok=True)` (no error if it already exists — see Hook Integration Model on why this is per-file, not directory-level), then for each file in `hupy/assets/hook-stubs/`: if the target already exists, without `force` → `logger.error(...)` + `raise SystemExit(1)` (leaving that and any later files untouched); with `force`, `logger.warning(...)` then overwrites; otherwise reads the template text, substitutes `{{PYTHON}}` with `sys.executable` (see Hook Integration Model), writes it, and `shutil.copymode` (preserves the executable bit, since the substitution is a text read/write rather than `shutil.copy2`)
     - `_run_create_config_file` calls `create_default_config_file(repo, args.force)` (`hupy/config_file/write_config.py`) — same existence/`force` pattern as the hooks step, but for a single file: `get_config_file_path(repo)`, `shutil.copyfile`d from the packaged asset `hupy/assets/.hupy.config.jsonc` rather than generated from `HupyConfigFile` defaults (see `config_file` in Module Details)
  - `_resolve_hooks_dir`/`_copy_hook_stubs` and their supporting constants (`_HOOK_STUBS_DIR`, `_PYTHON_PLACEHOLDER`) now live directly in `cli_init.py` — formerly in a separate `cli_ich.py` module (deleted along with `cli_icc.py`'s `init-create-config`; see `CHANGELOG.md` for the removal), which required a deferred, in-function import to avoid a circular import. That workaround is gone now that everything lives in one module
- **`verify-config-file`** — implemented in `cli_verify.py`; loads and validates the repo's `.hupy.config.jsonc` via `load_hupy_config(repo)`, logging success or letting the `SystemExit(1)` from a missing/malformed file propagate. Shares `load_git_repo`, `INIT_LOGGER_NAME`, and `REPO_PATH_HELP` from `cli_init.py`; takes the same `REPO_PATH`/`-v`/`-q` arguments as `init` but no `-f`/`--force` (it doesn't write anything)
- **`load_git_repo(repo_path)`** — `git.Repo(repo_path, search_parent_directories=True)`; on `InvalidGitRepositoryError`/`NoSuchPathError`, `logger.exception(...)` then `raise SystemExit(1) from e`, **before** any filesystem writes happen. Used by `init`, `verify-config-file` (both via their respective `_*_main`), and `config.load_hupy_config` (via `hupy.cli.cli_init.load_git_repo`), so all resolve the same way from any subdirectory of the repo
- **`init`/`verify-config-file` CLI arguments**: both share `REPO_PATH` (positional, optional, `type=pathlib.Path`, default=`pathlib.Path(os.getcwd())`, help text from the shared `REPO_PATH_HELP` constant) and `-v`/`-q` verbosity; `-f`/`--force` gates whichever selected step(s) `init` runs (not present on `verify-config-file`, which writes nothing); `--hooks-dir HOOKS_DIR` (`type=pathlib.Path`, default `None` → resolved in the copy-hooks step) and the step-selector flags `--copy-hooks`/`--create-config-file` (both `action="store_true"`, `dest`s matching the `_INIT_STEPS` registry) are `init`-only
- Known gap: `REPO_PATH`'s default is `pathlib.Path(os.getcwd())` evaluated once, when `register_cli_init_parser`/`register_cli_verify_parser` run at module-import time — not per invocation. In a long-lived process (or across a test session that imports these modules once) this default is frozen to whatever the cwd was at first import, not the cwd at call time, despite the help text's "default=current working directory" implying otherwise. `tests/cli/` works around this by always passing `REPO_PATH` explicitly rather than relying on the default
- Packaged templates: `hupy/assets/hook-stubs/{pre-commit,prepare-commit-msg,post-commit}` (thin `"{{PYTHON}}" -m hupy hook <stage>` wrappers, no `.bash` extension since git requires the exact hook name in the hooks directory) and `hupy/assets/.hupy.config.jsonc` (the default config content, see `config_file` in Module Details), bundled via `[tool.setuptools.package-data]` in `pyproject.toml` (`hupy = ["assets/hook-stubs/*", "assets/.hupy.config.jsonc"]`)
- **`pre-commit`** (`cli_pre_commit.py`) — builds `repo = git.Repo(os.getcwd(), search_parent_directories=True)`, then opens `hupy-state.json` via `with open_state_file(repo) as state_file:` (see `state` in Module Details) for the rest of its body: applies `-v`/`-q` verbosity on top of `state_file.logger_verbosity`, then calls `ban_direct_commit(repo, state_file)` followed by `perform_triage_tags_gating(repo, state_file)`; logs entry/exit via the logger (no nested subcommands). No longer loads `.hupy.config.jsonc` itself — each called function loads it internally via `should_run_module`/its own `load_hupy_config(repo)` call
- **`prepare-commit-msg`** (`cli_prepare_commit_msg.py`) — same `git.Repo`-build-then-`open_state_file`-then-verbosity pattern, then calls `prepend_commit_header(repo, state_file)`; as the last of the two hook stages in a commit round, its dispatch also calls `state_file.clear_skip_once()` right after its trailing hook bracket, spending the whole `skip_once` set for the round (see `state`/`should_run_module` in Module Details); logs entry/exit via the logger (no nested subcommands)
- **`skip-once`** (alias `s`, `cli_skip_once.py`) — flags one or more modules to be skipped for exactly the next `pre-commit`/`prepare-commit-msg` run. `SKIPPABLE_MODULE = ("vg", "ttg", "pch", "bdc", "hb")`; a local `_MODULE_ABBR_TO_NAME`/`_MODULE_NAME_TO_ABBR` pair maps each abbr to a kebab-case full name (`"vg"`↔`"ver-grep"`, `"ttg"`↔`"triage-tag-gating"`, `"pch"`↔`"prepend-commit-header"`, `"bdc"`↔`"ban-direct-commit"`, `"hb"`↔`"hook-bracket"` — distinct from `should_run_module`'s Title Case display names, see `should_run_module` in Module Details), so the `modules` positional argument (`nargs="+"`) accepts either form; `_skip_once_main` normalizes each to its abbr and calls `state_file.skip_once.update(abbrs)` inside `open_state_file(repo)`. Building `SKIPPABLE_MODULE`/the name maps is currently duplicated between here and `should_run_module.py`'s own `_MODULE_ABBR_TO_NAME` (different casing, same five abbrs) — not yet factored out to a shared location
- **dispatch functions are module-level**, each in their own module (`cli_pre_commit._pre_commit_main`, `cli_prepare_commit_msg._prepare_commit_msg_main`, `cli_verify._verify_main`, `cli_skip_once._skip_once_main`) — they call the public functions from `ttg.gate_tt`, `pch.prepend_commit_header`, `bdc.ban_direct_commit`, and `state.open_state.open_state_file` directly, not via a CLI re-entry
- **verbosity** — both hook-stage dispatch functions call `kamilog.set_logging_level_by_namespace(args, verbosity=state_file.logger_verbosity)`, so `hupy-state.json`'s `logger_verbosity` sets the baseline and each `-v`/`-q` shifts it by one step (this used to come from `.hupy.config.jsonc`'s now-removed `default_logger_verbosity` field — see `config_file` in Module Details); this targets the shared `PROJ_LOGGER_NAME` (`"HU"`) root logger, and child loggers (`"HU.TTG"`, `"HU.PCH"`, `"HU.CBM"`, `"HU.config-file"`, `"HU.VerGrep"`, `"HU.BDC"`) inherit the resulting level since they set none of their own. `cli_init.py`'s `init`, `cli_verify.py`'s `verify-config-file`, and `cli_skip_once.py`'s `skip-once` call the same function but without a state file (`set_logging_level_by_namespace(args, logger=logger)`, base `verbosity=0`), since none of them can assume `hupy-state.json`/`.hupy.config.jsonc` is loadable yet

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
- loggers created via `getLogger()` in `cbm` (`CBM_LOGGER_NAME`), `pch.prepend_commit_header`, `cli.cli_init`, `config.config_file` (`CONFIG_LOGGER_NAME`), `ver_grep`, and `ttg.gate_tt` each set `logger.propagate = False` — every logger already carries its own stdout/stderr handlers from `getLogger()`, so leaving propagation on would double-print every record through the root logger's handlers too
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
    cli_verify.py                  # `verify-config-file` subcommand
    cli_skip_once.py               # `skip-once`/`s` subcommand; SKIPPABLE_MODULE
  cbm/                             # Commit/Branch/Merge package (formerly flat commit_type.py)
    __init__.py                   # CBM_LOGGER_NAME = "HU.CBM"; re-exports below
    branch_type.py                 # BranchType enum + from_name(branch_name, repo)
    commit_type.py                 # CommitType flag + decide_commit_type(source, target)
    get_current_commit_type.py     # get_current_commit_type/get_source_branch/get_target_branch(repo)
  bdc/                             # Ban Direct Commit package
    __init__.py                   # BDC_LOGGER_NAME = "HU.BDC"; re-exports below
    ban_direct_commit.py           # ban_direct_commit(repo, state_file)
  config/                         # HUPy config schema, load, and write helpers
    __init__.py                   # CONFIG_LOGGER_NAME
    config_file.py                 # HupyConfigFile pydantic model (schema, no defaults); _VerGrep (exposed as `vg`); _Cbm; _Pch; _Bdc
    config_file_path.py            # CONFIG_FILENAME = ".hupy.config.jsonc"; DEFAULT_CONFIG_ASSET; get_config_file_path(repo)
    load_config.py                # load_hupy_config(repo): git.Repo in, read JSON5 + validate, cache
    write_config.py               # create_default_config_file(repo, force): copies the packaged asset below
  state/                          # HUPy state schema and file writing (hupy-state.json)
    __init__.py                   # STATE_LOGGER_NAME
    state_file.py                  # HupyStateFile pydantic model: logger_verbosity, skip_once; consume_skip_once(module_abbr), clear_skip_once()
    state_file_path.py             # STATE_FILENAME = "hupy-state.json"; get_state_file_path(repo) (inside repo.git_dir)
    open_state.py                  # open_state_file(repo): atomic, thread-/process-safe load+save context manager
  should_run_module.py            # should_run_module(repo, state_file, module_abbr): config is_disabled + state skip_once gate
  assets/                         # packaged non-code data files
    .hupy.config.jsonc             # default config content, commented; copied verbatim by create_default_config_file
    hook-stubs/                   # default hook stub scripts
      pre-commit                  # thin wrapper: `"{{PYTHON}}" -m hupy hook pre-commit`
      prepare-commit-msg          # thin wrapper: `"{{PYTHON}}" -m hupy hook prepare-commit-msg`
      post-commit                 # thin wrapper: `"{{PYTHON}}" -m hupy hook post-commit`
  kamilog.py                      # vendored logging module (v2.3.1)
  pch/                            # Prepend Commit Header package
    __init__.py                   # PCH_LOGGER_NAME = "HU.PCH"
    prepend_commit_header.py      # main function: rewrite COMMIT_EDITMSG; _HEADER_GENERATORS per merge type
  ttg/                            # Triage Tag Gating package
    __init__.py                   # TTG_LOGGER_NAME = "HU.TTG"
    triage_tag_type.py             # TriageTagType flag enum
    comment_style.py               # file extension -> comment-leader token
    detect_tt.py                  # scan staged diffs for TT markers, type-aware
    staged_files.py                # list staged files, filter ignored_path_globs
    report_tt.py                   # render/log gated TT findings
    gate_tt.py                     # gate commits by TT tier
  ver_grep/                       # version-grepping package (formerly flat ver_grep.py)
    __init__.py                   # VER_GREP_LOGGER_NAME = "HU.VerGrep"; re-exports below
    branch_version.py              # grep_source_branch_version()/grep_target_branch_version()
    version_bump.py                # decide_version_update_type(source_version, target_version)
docs/
  ttg_doc.md                      # user doc: TTG tiers & per-merge gating
  cbm_doc.md                      # user doc: CBM concepts + PCH merge-commit headers + ver_grep API
                                    # (config field docs now live as comments in hupy/assets/.hupy.config.jsonc)
examples/
  hooks/                           # bash demos driving the real `hupy <stage>` CLI end-to-end
    pre-commit-demo.sh             # Feature Landing merge, steady+quiet TT only; expects PASS
    prepare-commit-msg-demo.sh     # Version Release merge; expects header prepended
    all-hooks-demo.sh              # runs every demo in this folder in sequence (currently empty)
                                    # all three prep their repo by shelling out to tests/fixtures/prep_repo.py
  pch/                            # __init__.py (shared demo helpers) + 16 runnable demo scripts:
                                    # feature-landing, sync-backport, catch-up, hotfix-release,
                                    # hotfix-backport, release-cut, release-backport,
                                    # skip-regular-commit, skip-unrelated-merge, and 7 vr-*
                                    # (Version Release) scripts, one per release-type/bump-prefix
                                    # combination: vr-{alpha,beta,rc,fail-parse,minor-prototype,
                                    # minor-pre-alpha,major-stable}-demo.py
  ttg/                            # __init__.py (shared demo helpers) + 6 runnable demo scripts:
                                    # {pass,fail}-{feature-landing,version-release},
                                    # skip-{irrelevant-merge,non-merge-commit}
  bdc/                             # __init__.py (shared demo helpers) + 3 runnable demo scripts:
                                    # fail-direct-commit-to-main, pass-version-release-merge,
                                    # skip-non-protected-branch
tests/
  conftest.py                     # root-level shared `repo_dir` fixture (tmp_path / "repo")
  cbm/                             # CBM-specific tests
    conftest.py                   # sys.path shim onto tests/fixtures/ for config_fixture import
    cbm-branch_type_test.py        # BranchType.from_name classification & config precedence
    cbm-commit_type_test.py        # CommitType.decide_commit_type over all branch-type pairs
    grct/                          # get_current_commit_type/get_source_branch/get_target_branch tests
      conftest.py
      cbm-grct-get_current_commit_type_test.py
      cbm-grct-get_source_branch_test.py
      cbm-grct-get_target_branch_test.py
  vg/                              # ver_grep-specific tests
    conftest.py
    vg_helpers.py                  # shared merge-repo-with/without-version-file builders
    vg-decide_version_update_type_test.py
    vg-grep_source_branch_version_test.py
    vg-grep_target_branch_version_test.py
  cli/                            # cli (init subcommand + hook stub install) tests
    conftest.py                   # `git_repo_dir` fixture (builds on root `repo_dir`)
    cli_helpers.py                 # `run_init_cli`, `get_configured_hooks_path`,
                                    # `set_configured_hooks_path` helpers
    cli-cli_init_copy_hook_stubs_test.py
    cli-cli_init_resolve_hooks_dir_test.py
    cli-cli_init_init_cli_test.py
  config/                         # config-package-specific tests
    config-shipped_config_file_test.py  # shipped .hupy.config.jsonc asset validates & version matches
  state/                           # state-package-specific tests
    state-consume_skip_once_test.py  # HupyStateFile.consume_skip_once
  should_run_module/               # tests for the top-level should_run_module.py (no enclosing package)
    conftest.py                    # sys.path shim onto tests/fixtures/ for config_fixture import
    should_run_module_test.py      # is_disabled/skip_once combinations across all 5 skippable modules
  pch/                            # PCH-specific tests
    conftest.py                   # sys.path shim onto tests/fixtures/ for prep_repo import
    pch_helpers.py                # COMMIT_EDITMSG seed/read helpers
    pch-prepend_commit_header_skip_test.py
    pch-prepend_commit_header_feature_landing_test.py
    pch-prepend_commit_header_version_release_test.py
    pch-prepend_commit_header_error_test.py
  ttg/                            # TTG-specific tests
    conftest.py                   # sys.path shim onto tests/fixtures/ for prep_repo import
    fixtures/                     # per-scenario fixture files used by prep_repo.py (tt_*.py, ...)
    ttg-comment_style_test.py
    ttg-detect_tt_test.py
    ttg-gate_tt_feature_landing_test.py
    ttg-gate_tt_version_release_test.py
    ttg-gate_tt_non_merge_test.py
    ttg-gate_tt_regular_merge_test.py
    ttg-gate_tt_ignored_globs_test.py
    ttg-gate_tt_error_test.py     # patches hupy.ttg.staged_files.subprocess.check_output
  bdc/                             # BDC-specific tests
    conftest.py                   # sys.path shim onto tests/fixtures/ for config_fixture import
    bdc-ban_direct_commit_test.py
  fixtures/                       # fixtures shared by every suite (not package-specific)
    default_repo.bundle           # minimal git bundle fixture for repo cloning
    prep_repo.py                  # scenario repo generator (CLI + importable); also writes .hupy.config.jsonc
    config_fixture.py             # load_config_fixture(overrides): deep-merges overrides onto the shipped hupy/assets/.hupy.config.jsonc
.hupy.config.jsonc                # this repo dogfoods hupy on itself; includes cbm section
pyproject.toml
```

### Testing Infrastructure

- **pytest fixtures** (`repo_dir`) — path under `tmp_path` for the scenario repo, populated by `prep_repo.py`; defined once in the root `tests/conftest.py` and shared by every suite (`tests/cli/conftest.py`'s `git_repo_dir` builds on it); fixtures are scoped per-test and auto-cleaned by `tmp_path`
- **git bundle fixture** (`tests/fixtures/default_repo.bundle`) — minimal single-file repo fixture; `prep_repo.py` clones it and dynamically constructs scenarios (branches, commits, MERGE_HEAD state, staged files from `tests/ttg/fixtures/*.py`)
- **`tests/fixtures/prep_repo.py`** — the shared repo-scenario builder, used by `tests/pch/`, `tests/ttg/` unit tests and, indirectly, by the `examples/pch/*-demo.py` and `examples/ttg/*-demo.py` demos. Exposes three builders: `prepare_repo(dest_dir, scenario)` for the legacy TTG/PCH `SCENARIOS` that unit tests also exercise (`non_merge_commit`, `irrelevant_merge`, `feature_landing_{pass,fail}`, `version_release_{pass,fail}`), `prepare_repo_with_files(dest_dir, commit_bucket, files)` for an arbitrary file manifest against one of the `COMMIT_BUCKETS` (used by both unit tests and the `examples/ttg/*-demo.py` scripts), and `prepare_demo_repo(dest_dir, demo_bucket)` for the demo-only `DEMO_BUCKETS` — six merge types (`sync_backport`, `catch_up`, `hotfix_release`, `hotfix_backport`, `release_cut`, `release_backport`) with no dedicated `tests/pch/` assertions yet, only `examples/pch/*-demo.py` scripts, plus seven `release_*` buckets (`release_fail_parse`, `release_minor_prototype`, `release_alpha`, `release_beta`, `release_rc`, `release_major_stable`, `release_minor_pre_alpha`) that back the `vr-*-demo.py` scripts specifically, each pinning a Version Release release-type/bump-prefix combination. Also runnable standalone as a CLI with mutually exclusive `--scenario <name>` / `--demo-bucket <name>` flags plus `--dest`, printing the prepared repo path; `examples/hooks/prepare-commit-msg-demo.sh` shells out to this CLI rather than re-implementing repo setup in bash.
- **`examples/pch/__init__.py`** / **`examples/ttg/__init__.py`** — aux helpers shared across each directory's `*-demo.py` scripts, deduplicated out of what was previously identical `_prepare_demo_repo`/`_run_*` code copy-pasted into every demo file. Each does the `sys.path.insert` onto `tests/fixtures/` and wraps `prep_repo.py`'s builders (`prepare_demo_repo_by_scenario`/`prepare_demo_repo_by_bucket` + `run_pch` for `pch`; `prepare_demo_repo` + `run_ttg` for `ttg`, the latter calling `perform_triage_tags_gating` directly rather than the full `pre-commit` CLI). Demo scripts pull these in with `from __init__ import ...` — this resolves because Python auto-adds a directly-run script's own directory to `sys.path`, so no additional path wiring is needed in the demo files themselves.
- **test file naming** — nested-package modules follow `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py` (e.g. `hupy/ttg/gate_tt.py` → `tests/ttg/ttg-gate_tt_*_test.py`, `hupy/cbm/branch_type.py` → `tests/cbm/cbm-branch_type_test.py`, `hupy/ver_grep/branch_version.py` → `tests/vg/vg-grep_*_branch_version_test.py`, `hupy/state/state_file.py` → `tests/state/state-consume_skip_once_test.py`), split further by scenario group; `hupy/cbm/get_current_commit_type.py`'s three public functions each get their own file, nested under `tests/cbm/grct/` (the abbreviation mirrors the module name). A top-level module with no enclosing package (`hupy/should_run_module.py`) still gets its own directory under `tests/`, dropping the `<pkg>-` filename prefix since there's no package to name it after (`tests/should_run_module/should_run_module_test.py`). `ttg.staged_files` and `ttg.report_tt` have no dedicated test file of their own — both are exercised indirectly through the `ttg-gate_tt_*_test.py` suites (`staged_files.get_staged_file_paths`'s git-error path is covered by `ttg-gate_tt_error_test.py`, which patches `hupy.ttg.staged_files.subprocess.check_output`)
- **`tests/cli/`** (formerly `tests/setup/`, renamed with the `hupy/setup/` → `hupy/cli/` move) — unit tests for `_copy_hook_stubs` and `_resolve_hooks_dir` each get their own file (`cli-cli_init_copy_hook_stubs_test.py`, `cli-cli_init_resolve_hooks_dir_test.py`); both now import their targets from `cli_init.py` directly, since `cli_icc.py`/`cli_ich.py` were deleted and those helpers moved there. The copy-stubs file also covers the `{{PYTHON}}` → `sys.executable` substitution (placeholder replaced, baked path absolute, packaged templates still carry the placeholder — see `cli` in Module Details). `create_default_config_file` (in `hupy/config_file/write_config.py`) has no dedicated test file of its own (see `config_file` in Module Details) and is instead exercised via `cli-cli_init_init_cli_test.py`, which asserts the written file is byte-identical to the packaged asset (`hupy/assets/.hupy.config.jsonc`), rather than matching a serialized `HupyConfigFile()`. `cli-cli_init_init_cli_test.py` covers the CLI wiring end-to-end, since that's the other meaningful public surface (unlike `ttg`/`pch`, which test their public function directly without a separate CLI-wiring suite) — `cli_helpers.run_init_cli(args_list)` (formerly `setup_helpers.py`) builds a standalone `init` subparser via `register_cli_init_parser` and dispatches through it, exercising `--hooks-dir`/`--copy-hooks`/`--create-config-file`/`-f`/`-v`/`-q` the same way the real `hupy` CLI would; a `TestInitStepFlags` class asserts `--copy-hooks` alone skips the config file, `--create-config-file` alone skips the hooks, both flags together (or neither) produce both; `git_repo_dir` (in `conftest.py`) gives a fresh `git.Repo.init`-ed repo rather than reusing `ttg`'s scenario-bucket fixtures, since `init` doesn't care about commit type or branch state. Tests always pass `REPO_PATH` explicitly rather than relying on its default, since that default is frozen at module-import time (see `cli` in Module Details). 29 tests total; no dedicated test file exists yet for `cli_verify.py`'s own subcommand wiring (its behavior is exercised indirectly through `init`'s shared helpers).
- **`tests/cbm/`** — `cbm-branch_type_test.py` patches `hupy.cbm.branch_type.load_hupy_config` to stub `_Cbm` config, built via `tests/fixtures/config_fixture.py`'s `load_config_fixture(overrides)` rather than constructing `HupyConfigFile` directly (its fields carry no defaults any more — see `config_file` in Module Details), covering default and overridden branch names/prefixes and precedence between DEV/MAIN/HOTFIX/RELEASE/USER/FEATURE, and confirming `repo` is forwarded through to `load_hupy_config`; `cbm-commit_type_test.py` parametrizes `CommitType.decide_commit_type` over all 8 known `(BranchType, BranchType)` pairs plus a set of unmapped pairs (all → `OTHER_MERGE`); `grct/` covers `get_current_commit_type`/`get_source_branch`/`get_target_branch` against real repo fixtures — regular commits, octopus/pull merges, detached HEAD, and per-repo caching behavior — with `grct/conftest.py` noting that repo construction/error handling is the caller's job, not these functions'.
- **`tests/vg/`** — `vg-decide_version_update_type_test.py` covers major/minor/patch bump classification, no-update and unparsable cases, and pre-release/build-suffix stripping; `vg-grep_source_branch_version_test.py`/`vg-grep_target_branch_version_test.py` (mirror images of each other) patch `hupy.ver_grep.branch_version.load_hupy_config` and use shared `vg_helpers.py` fixtures (`prepare_merge_repo_with_version`, `prepare_merge_repo_without_version_file`) to assert each function reads its own branch's tip specifically (not the other branch's, not the working tree), first-match-wins, not-configured returning `""`, and `SystemExit` on a missing version file or no matching line.
- **`tests/state/state-consume_skip_once_test.py`** — direct unit tests on `HupyStateFile.consume_skip_once`/`clear_skip_once`, no config/repo fixtures needed: not-flagged returns `False` without mutating `skip_once`; flagged returns `True` without discarding the entry (siblings untouched, a second `consume_skip_once` call for the same `module_abbr` still returns `True`); `clear_skip_once` empties the whole set (no-op when already empty).
- **`tests/should_run_module/should_run_module_test.py`** — patches `hupy.should_run_module.load_hupy_config` (a separate patch target from each consuming module's own `load_hupy_config` reference, since Python binds `from ... import` at each call site) and constructs `HupyStateFile` instances directly, parametrized across all 5 entries in `should_run_module`'s `_MODULE_ABBR_TO_NAME`. Asserts: enabled + unflagged runs; `is_disabled` blocks regardless of `skip_once`; `skip_once` blocks and is left set (not consumed — only the matching entry, siblings left alone); `is_disabled` is checked first and short-circuits *without* consuming a pending `skip_once` flag; a second call within the same round still skips (flag stays set); and a call after `clear_skip_once()` runs normally (flag spent at round end).
- **`tests/bdc/bdc-ban_direct_commit_test.py`** — patches `hupy.bdc.ban_direct_commit.load_hupy_config`/`get_target_branch`/`get_current_commit_type` (rather than building a real repo fixture, since `ban_direct_commit` only needs config values and a branch/commit-type pair) to assert: an unprotected branch, a `dev`/`main` branch with its `ban_commit_to_*` flag disabled, and a detached HEAD (`current_branch=None`) are all skipped; a `dev`/`main` name read from the `cbm` config (not hardcoded `"dev"`/`"main"`) and an entry in `ban_commit_to_branches` are all protected; and, once protected, a non-merge commit raises `SystemExit(1)` while a merge commit of any `CommitType` (`FEATURE_LANDING`, `VERSION_RELEASE`, `OTHER_MERGE`) is allowed. 11 tests total. `examples/bdc/__init__.py` provides two demo-repo builders exercised by the 3 `examples/bdc/*-demo.py` scripts: `prepare_demo_repo_by_bucket` (reuses `prep_repo.py`'s `COMMIT_BUCKETS` for a passing merge scenario) and `prepare_demo_repo_on_branch` (clones the shared bundle, checks out a fresh unprotected branch, commits directly on it — the fail/skip scenarios), plus `run_bdc` which calls `ban_direct_commit` directly and swallows the `SystemExit` it raises on failure.
- **`tests/pch/pch-prepend_commit_header_version_release_test.py`** — patches `hupy.pch.prepend_commit_header.grep_source_branch_version`/`grep_target_branch_version` (rather than `load_hupy_config`, since the version-string plumbing is already covered by `tests/vg/`) to assert: plain `"Version Release"` with no source version, plain `"Version Release: <version>"` on an unparsable version, and — in `TestVersionReleaseHeaderScenarios` — all 7 release-type/bump-prefix combinations (Alpha, Beta, Release Candidate, Pre-Alpha, Prototype, Stable, each with/without a bump prefix as applicable). 24 tests total in `tests/pch/`, 12 in this file. The 6 newer merge types (`SYNC_BACKPORT`, `CATCH_UP`, `HOTFIX_RELEASE`, `HOTFIX_BACKPORT`, `RELEASE_CUT`, `RELEASE_BACKPORT`) still have no equivalent dedicated test file — only `examples/pch/*-demo.py` scripts exercise them, one per type.
