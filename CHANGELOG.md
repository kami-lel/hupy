# hupy CHANGELOG

[^format]

## [Unreleased]

### Added

- **`verify-config-file`** — new `hupy` subcommand that loads and validates the repo's `.hupy.config.jsonc` against `HupyConfigFile`, reporting success or the validation error
- **config version-mismatch warning** — loading a config file whose `hupy_version` doesn't match the installed `HUPy` version now logs a warning
- **`--copy-hooks`/`--create-config-file` flags on `hupy init`** — run either step alone, or both together (same as passing neither); a step registry in `cli_init.py` makes adding further steps/flags a one-line change
- **per-module `is_disabled` config flag** — `vg`, `ttg`, `pch`, and `bdc` each gain an `is_disabled: bool` field in `.hupy.config.jsonc` (`vg`'s validator still returns early without the unconfigured-warning when disabled); consumed by the new centralized run-gating below — `hb` already carried the field from `dev` but has no implementation yet to wire it into
- **new `ttg` config section** — `is_disabled`, `disable_tt_detect_by_type`, `ignored_path_globs`; all three are now consumed by `ttg.gate_tt`/`ttg.detect_tt`: `disable_tt_detect_by_type` (default `false`) requires a TT tag to follow the comment-leader token expected for the file's extension (eg `//`, `#`, `<!--`), via the new `ttg.comment_style.get_comment_prefix_for_file`, rather than matching anywhere in the line; `ignored_path_globs` skips matching staged files from TT scanning entirely
- **HUPy state file** (`hupy-state.json`) — new `hupy.state` package: `HupyStateFile` schema (`hooks_logger_verbosity`, `skip_once`), resolved via `get_state_file_path(repo)` inside the repo's `.git` directory; `open_state_file(repo)` opens and atomically saves it back, thread- and process-safe via a file lock plus a `tempfile`/`os.replace` write; a missing file falls back to schema defaults
- **`skip-once`/`so`** CLI subcommand — flags one or more modules (`vg`/`ttg`/`pch`/`bdc`/`hb`, or their full names like `ver-grep`/`triage-tag-gating`) to be skipped for the next commit round, recorded in `hupy-state.json`'s `skip_once` set; the new `-u`/`--unset` flag removes the flag(s) instead of setting them
- **centralized module run-gating** — new `should_run_module(repo, state_file, module_abbr)` combines a module's config `is_disabled` flag with a one-time `skip_once` flag (a plain membership check against `HupyStateFile.skip_once`, which stays set for every call across a round, since a module like `hb` is checked multiple times per round) into a single decision; `is_disabled` is checked first and short-circuits before the `skip_once` check; `ban_direct_commit`, `perform_triage_tags_gating`, and `prepend_commit_header` each take a new `state_file` parameter and call it in place of their own former direct `is_disabled` check; the whole `skip_once` set is spent by the new `HupyStateFile.reset_for_next_commit()`, called from the new `post-commit` hook stage below
- **`post-commit` hook stage** — new `hupy hook post-commit` subcommand, wired into the `post-commit` git hook stub, that resets one-time state (`skip_once`) for the next commit round via `HupyStateFile.reset_for_next_commit()`; `examples/hooks/post-commit-demo.sh` demonstrates it, and `all-hooks-demo.sh` now runs it
- **`hb` post-commit bracket** — `_Hb` gains a `post_commit: _HbBracket` field (`hb.post_commit.lead`/`.trail` in `.hupy.config.jsonc`), and `_Hb.get_bracket` recognizes `"post-commit"`; `hook post-commit` now runs `perform_hook_brackets(repo, state_file, "post-commit", True)` then the `False` (trail) call, bracketing `state_file.reset_for_next_commit()` the same way `hb` already brackets `pre-commit`/`prepare-commit-msg`
- **`set-verbosity`/`sv`** CLI subcommand — sets `hooks_logger_verbosity` in `hupy-state.json`, controlling log verbosity for subsequent hook runs

### Changed

- config file renamed **`.hupy.config.json`** → **`.hupy.config.jsonc`**, now parsed as JSON5 (comments and trailing commas allowed) via the new `json5` dependency
- `hupy init`/`init-create-config` now write a fresh config by copying a packaged asset (`hupy/assets/.hupy.config.jsonc`) verbatim, rather than generating one from `HupyConfigFile`'s field defaults; `HupyConfigFile`'s fields no longer carry defaults themselves — the shipped asset is now the single source of default values, with its comments documenting each field in place of the old `docs/hupy_config_doc.md`
- renamed `write_default_config` → `create_default_config_file` (now takes a `git.Repo`, not a bare `repo_root` path); renamed `hupy/config/hupy_config_file.py` → `hupy/config_file/config_file.py`, and the `hupy.config` package itself renamed to `hupy.config_file`
- git hook stage subcommands (`pre-commit`, `prepare-commit-msg`) moved from top-level `hupy <stage>` into a new `hupy hook <stage>` subcommand group (`hupy/cli/hook/` package), alongside the new `post-commit` stage above
- **`ttg` package restructured** — `ttg.tt_gating` renamed to `ttg.gate_tt`, `ttg.tt_detect` renamed to `ttg.detect_tt`; `ttg.gate_tt` further split into `ttg.staged_files` (staged-file listing and `ignored_path_globs` filtering) and `ttg.report_tt` (rendering/logging gated-tag findings), leaving `gate_tt` holding just the gating decision itself; `triage_tag_type.py` trimmed down to the bare `TriageTagType` flag enum — its line-scanning logic moved into `detect_tt` (its only caller) and the redundant `filter_by_group` classmethod removed in favor of `TriageTagType`'s native `in`-based group membership check
- `ttg`/`pch` auxiliary functions that need config values now call the cached `load_hupy_config(repo)` directly instead of having the value threaded down through function parameters
- `default_logger_verbosity` removed from `HupyConfigFile`; verbosity now comes from `hupy-state.json`'s `hooks_logger_verbosity` field instead, read by each `hupy hook` stage through the new `open_state_file` context, and set via the new `set-verbosity`/`sv` CLI subcommand above
- config field `ver_grep` renamed to **`vg`** (schema field, JSON key in `.hupy.config.jsonc`, and all references) — aligns with the `vg` abbreviation already used by `skip-once`
- config path constants/helpers (`CONFIG_FILENAME`, `DEFAULT_CONFIG_ASSET`, `get_config_file_path`) extracted out of `load_config.py`/`write_config.py` into a new `hupy/config_file/config_file_path.py`

### Deprecated

### Removed

- `docs/hupy_config_doc.md` (folded into `.hupy.config.jsonc`'s own comments)
- **`init-create-config`/`init-copy-hooks` subcommands** — superseded by `hupy init`'s new `--create-config-file`/`--copy-hooks` flags; `cli_icc.py`/`cli_ich.py` deleted, their `_copy_hook_stubs`/`_resolve_hooks_dir` helpers and supporting constants moved into `cli_init.py`

### Fixed

### Security



## [0.3.0] - 2026-07-10

### Added

- **`init-create-config`** and **`init-copy-hooks`** — new `hupy` subcommands that split `init` into standalone steps: writing the default `.hupy.config.json` alone, or copying the hook stub scripts alone
- **six new merge types recognized** — `hupy.pch` now prepends commit headers for Sync Backport, Catch Up, Hotfix Release, Hotfix Backport, Release Cut, and Release Backport, alongside the existing Feature Landing and Version Release headers — 8 merge types total, each with its own header format and, where applicable, a version number
- **configurable branch names** — new `cbm` section in `.hupy.config.json` (`main_branch_name`, `dev_branch_name`, `hotfix_branch_prefix`, `release_branch_prefix`) replaces hardcoded `"main"`/`"dev"` branch matching
- **version-bump detection** — `pch` classifies a merge's major/minor/patch version bump and prefixes it onto the Version Release, Hotfix Release, and Release Cut headers
- **release-type detection in the Version Release header** — classifies the source version as Alpha, Beta, Release Candidate, Pre-Alpha, Vertical Slice, Prototype, or Stable and labels the header accordingly, eg `Minor Prototype Release: 0.4.0`, `Alpha Release: 1.3.0-alpha.1`
- **`pch` config section** — new section in `.hupy.config.json` (`enable_vertical_slice`, `enable_pre_alpha`, `alpha_tag`, `beta_tag`, `release_candidate_tag`) configures which release types `pch` recognizes
- **Ban Direct Commit** — a `pre-commit` check, wired ahead of Triage Tag Gating, that blocks a commit made directly on a protected branch (`main` by default) while still allowing that branch to receive commits through a merge; a new `bdc` section in `.hupy.config.json` (`ban_commit_to_dev`, `ban_commit_to_main`, `ban_commit_to_branches`) configures which branches are protected

### Changed

- `hupy init` now composes `init-create-config` and `init-copy-hooks`; behavior is unchanged, but each step can also be run standalone
- `init`'s positional repo argument renamed from `REPO_ROOT` to `REPO_PATH` (help text only; behavior unchanged)
- renamed generated commit-header terminology: **Feature Finish** → **Feature Landing**, **Version Release** → **Stable Release**, then reverted **Stable Release** back to **Version Release**
- restructured `hupy.commit_type` (flat module) into the `hupy.cbm` package (Commit/Branch/Merge)
- restructured `hupy.ver_grep` (flat module) into a package that reads each branch's tip via `git show` rather than the working tree
- consolidated `docs/pch_doc.md` into a new `docs/cbm_doc.md` guide covering Branch/Merge concepts, PCH headers, and `ver_grep`
- Catch Up header now includes the target branch name, previously plain `"Catch Up"`
- `hupy pre-commit`'s and `hupy prepare-commit-msg`'s log lines reworded for consistency

### Removed

- `docs/pch_doc.md` (folded into `docs/cbm_doc.md`)

### Fixed

- `examples/{pch,ttg}/*.bash` demo scripts rewritten as executable `.py` scripts; also fixes them actually running their hook (previously errored on a stray CLI argument, and the demo repos never had a `.hupy.config.json` for the hook to load)

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.3.0...dev
[0.3.0]: https://github.com/kami-lel/hooks-utility-py/compare/v0.2.0...v0.3.0













## [0.2.0] - 2026-07-08

First version. **HUPy** is a ground-up Python reimplementation of the original bash [hooks-utility](https://github.com/kami-lel/hooks-utility), repackaging its git-hook commit-quality checks as an installable `hupy` command-line tool.

### Added

- **One-command setup** — `pip install` then `hupy init` drops the git hook stubs into a repository and writes a tracked `.hupy.config.json`; from then on the hooks run automatically on every commit
- **Triage Tag Gating** — a `pre-commit` check that blocks merges into protected branches when the staged changes still contain unfinished-work markers (`TODO`, `FIXME`, `HACK`, `BUG`), by severity tier: Loud when finishing a feature into `dev`, Loud and Steady when releasing to `main`
- **Prepend Commit Header** — a `prepare-commit-msg` step that automatically adds a descriptive header to Feature Finish and Stable Release merge commits, stamping the project version on releases
- **Version detection** — reads the project's version from a file you configure, matched by a regular expression, for use in the release commit header
- **Commit-type detection** — recognizes the kind of in-progress commit (Feature Finish, Stable Release, or ordinary) from git state, shared by both hooks
- **Configurable behavior** — a tracked `.hupy.config.json` controls log verbosity and the version lookup, so every clone of a repository behaves the same
- **Documentation and examples** — a README quick-start, per-feature guides under `docs/`, and runnable demo scripts under `examples/`

[0.2.0]: https://github.com/kami-lel/hooks-utility-py/releases/tag/v0.2.0













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
