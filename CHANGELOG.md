# hupy CHANGELOG

[^format]

## [Unreleased]

### Added

- **HB command `timeout`** — an HB command's config entry (`.hupy.config.jsonc`) accepts an optional `timeout` (float, seconds); exceeding it fails the command, honoring the entry's `allow_failure`
- **Hook argument passthrough** — every hook stub now forwards git's own hook arguments (`"$@"`) into `hupy hook <stage>`, which threads them (shell-quoted) onto every HB bracket command's `cmd`; re-run `hupy init --install-hook-stubs --force` to pick up the updated stubs
- **14 new git hook stages** — `commit-msg`, `pre-merge-commit`, `post-merge`, `pre-rebase`, `post-rewrite`, `applypatch-msg`, `pre-applypatch`, `post-applypatch`, `pre-auto-gc`, `post-index-change`, `sendemail-validate`, `fsmonitor-watchman`, `post-checkout`, and `pre-push` join `pre-commit`, `prepare-commit-msg`, and `post-commit`, bringing every git client-side hook under `hupy hook <stage>`; each gets its own `hb` bracket config section, though only four stages run any *HUPy* feature beyond their Hook Bracket (see **Triage Tag Gating in `pre-merge-commit`** below)
- **Triage Tag Gating in `pre-merge-commit`** — a conflict-free merge never visits `pre-commit`, so TTG now also gates `pre-merge-commit`, the other stage where a merge commit can actually be created; **Feature Landing** and **Version Release** are gated there exactly as they already were in `pre-commit`
- **Demand-driven hook stubs** — `get_hook_names_by_demand` now auto-discovers every stage module under `hupy.cli.hooks` and installs a stub only when demanded: its `hb` bracket is enabled with a `lead`/`trail` command configured (`_HbBracket.should_install_hook_stub()`), or its module defines `run_features`/`run_after`; by default that's still only `pre-commit`, `prepare-commit-msg`, `post-commit`, and `pre-merge-commit`, but any of the 17 stages now gets a stub automatically once its Hook Bracket is configured
- **Chain diagrams** — `docs/chain_doc.md` gained Mermaid diagrams for the Commit Chain (covering both `git commit` and `git rebase`) and the Merge Chain, plus the Patch Apply Chain and a Standalone Hooks list, covering the full set of seventeen stages
- **`docs/stub_doc.md`** — hook-stub auto-determination and `hupy init`/`hupy verify` stub management, split out into its own doc and linked from the README rather than described ad hoc
- **`hupy get`/`set`/`unset`/`info` accessor commands** — a generic state-key accessor layer replaces the standalone `skip-once`/`set-verbosity` subcommands; each key (`hupy-version`, `verbosity`, `skip-once`) is its own module under `hupy/cli/accessors/` exposing `KEY`/`DOC` plus whichever of `run_get`/`run_set`/`run_unset`/`run_info` it supports, auto-nested as a subcommand under the matching top-level verb by the generic `hupy/cli/cli_accessors.py` runner
- **`hupy-version` accessor key** (`hupy get hupy-version`, `hupy info hupy-version`) — prints the installed *HUPy* package version
- **`--version`** flag on the top-level `hupy` command — prints the installed package version directly
- **`hupy set verbosity` offsets via `-v`/`-q`** — every accessor subcommand already accepted `-v`/`-q` to adjust its own invocation's logging; `set verbosity` now folds that same count into the value it persists (`VALUE + verbose - quiet`, `VALUE` defaulting to the schema default when omitted), so e.g. `hupy set verbosity -vv` bumps the stored base by two without having to know its current value
- **Chain demo scripts** — `examples/chain/` gained `rebase-chain-demo.sh` (`pre-rebase` → `post-rewrite`), `merge-chain-demo.sh` (`pre-merge-commit` → `prepare-commit-msg` → `commit-msg` → `post-commit` → `post-merge`), and `patch-apply-chain-demo.sh` (`applypatch-msg` → `pre-applypatch` → `post-applypatch`), each driving `hupy hook <stage>` end-to-end against a fixture repo; `commit-chain-demo.sh` gained its previously-missing `commit-msg` stage and now runs its chain once, forwarding any `-v`/`-q` flags into a single `hupy set verbosity` call up front rather than passing them to every hook invocation

### Changed

- **`hupy skip-once`/`so` → `hupy set skip-once` / `hupy get skip-once` / `hupy unset skip-once`**; **`hupy set-verbosity`/`sv` → `hupy set verbosity` / `hupy get verbosity`** — folded into the new accessor key layer, each gaining a matching `hupy info <key>` subcommand

- HB bracket commands now run explicitly under `/bin/bash` (previously the platform's default shell) and receive a copy of the parent process's environment
- Every `hb` config section (one per hook stage) is now optional and defaults to empty `lead`/`trail` lists; `is_disabled` defaults to `false`. Previously only `pre-commit`, `prepare-commit-msg`, and `post-commit` existed and all three had to be spelled out
- `cli/hook/` restructured from one file per subcommand (`cli_pre_commit.py`, `cli_prepare_commit_msg.py`, `cli_post_commit.py`) into one file per git hook stage (package renamed `hook/` → `hooks/`) plus a shared generic runner, `hupy/cli/cli_hook.py`, so a new stage needs only a stage module declaring `HOOK_NAME` (and, optionally, `run_features`/`run_after`) and a registration call — the runner builds the subcommand's help text from `HOOK_NAME` and creates/passes a shared project logger and a per-stage logger into `run_features`/`run_after` as `(repo, state_file, proj_logger, logger)`, so stage modules no longer declare their own `DOC` or logger
- `hupy init`'s hook-stub install step now renders each stub in-process from the demanded hook names (`hupy.stub.names_by_demand.get_hook_names_by_demand`) rather than copying bundled `hupy/assets/hook-stubs/` template files; its flag renamed **`--copy-hooks` → `--install-hook-stubs`**
- `hupy verify` gains **`-u`/`--update-hook-stubs`** (sync installed hook stubs to demand: add missing, remove no-longer-demanded) and **`-f`/`--force`** (with `-u`, also regenerate already-installed demanded stubs); previously it only checked that every packaged stub existed
- `hupy.stub.update_stubs`'s `install_hook_stubs`/`verify_hook_stubs` now take a `repo` directly and resolve its hooks directory internally via a new public `resolve_hooks_dir(repo)`, rather than requiring the caller to resolve it first; `get_hook_names_by_demand` likewise now takes a `repo`
- `load_hupy_config` gains an `allows_file_not_found` flag, returning `None` instead of exiting when the config file is missing; any malformed content, not just a schema-validation failure, still exits
- each hook stage's finish log now reads `"{stage} stage Finished"` at the `done` level (previously a plain `"Finished"` succ log); the `on_done` callback and post-commit's `run_done` hook it briefly grew are gone again — a stage's own finish log covers that role

### Deprecated

### Removed

- bundled `hupy/assets/hook-stubs/*` template files — hook stub content is now rendered in-process rather than copied from disk
- `hupy/cli/cli_skip_once.py`, `hupy/cli/cli_set_verbosity.py` — superseded by `hupy/cli/accessors/skip_once.py`, `hupy/cli/accessors/verbosity.py`, and the generic `hupy/cli/cli_accessors.py` runner

### Fixed

### Security

[unreleased]: https://github.com/kami-lel/hupy/compare/v1.0.0...dev













## [1.0.0] - 2026-07-12

First stable release.

### Added

- **Hook Bracket (HB)** — run your own *lead* and *trail* shell commands around each hook stage (`pre-commit`, `prepare-commit-msg`, `post-commit`) straight from `.hupy.config.jsonc`, with no custom hook script; each command can filter by commit type and choose whether its failure blocks the commit
- **`hupy verify`** (alias `v`) — checks a repository's setup in one command: the config file loads and validates, the version string is greppable, and every packaged hook stub is installed in the hooks directory
- **`hupy skip-once`** (alias `so`) — skip one or more modules (`vg`/`ttg`/`pch`/`bdc`/`hb`) for just the next commit without editing the config; `-u`/`--unset` clears a pending skip
- **`hupy set-verbosity`** (alias `sv`) — set the hook log verbosity, remembered across commits
- **`post-commit` hook stage** — a third git hook stage, added alongside `pre-commit` and `prepare-commit-msg`, that clears one-time state after a commit lands and runs its own Hook Bracket
- **Per-module disable switch** — an `is_disabled` flag on every feature (`vg`/`ttg`/`pch`/`bdc`/`hb`) turns it off without removing its configuration
- **Selectable `hupy init` steps** — `--copy-hooks` and `--create-config-file` each run one setup step alone; plain `hupy init` still runs both
- **Comment-aware Triage Tag Gating** — a new `ttg` config section adds `disable_tt_detect_by_type` (only count a triage tag that follows the file's comment leader, e.g. `//`, `#`, `<!--`) and `ignored_path_globs` (exclude matching files from scanning)
- **Config version check** — loading a config file whose `hupy_version` differs from the installed *HUPy* version now logs a warning

### Changed

- Config file renamed **`.hupy.config.json` → `.hupy.config.jsonc`**, now parsed as JSON5 so it can carry `//` comments and trailing commas; the shipped file documents every field inline
- The shipped `.hupy.config.jsonc` is now the single source of default values — `hupy init` writes it verbatim, and the config schema no longer carries its own field defaults
- Git hook stages moved from top-level `hupy <stage>` into a **`hupy hook <stage>`** command group (`pre-commit`, `prepare-commit-msg`, `post-commit`)
- Config field `ver_grep` renamed to **`vg`**, matching the abbreviation used elsewhere
- Log verbosity now comes from the local `hupy-state.json` (set via `set-verbosity`) rather than a config-file field
- Ban Direct Commit log messages now name the branch involved

### Removed

- **`init-create-config` / `init-copy-hooks` subcommands** — replaced by `hupy init`'s new `--create-config-file` / `--copy-hooks` flags
- `docs/hupy_config_doc.md` — its field documentation now lives inline in `.hupy.config.jsonc`

### Fixed

- Prepend Commit Header could misclassify an unparsable version (e.g. `v2024.07-rc1`) as a tagged pre-release; version tags are now only recognized once a `major.minor.patch` core matches
- State log lines printed twice due to logger propagation; now emitted once
- `verify`'s log lines were mislabeled under the init logger and its verbosity flags misapplied; it now uses its own logger
- Several `examples/` demo scripts failed to write a `.hupy.config.jsonc` and errored instead of demonstrating their feature

[1.0.0]: https://github.com/kami-lel/hupy/compare/v0.3.0...v1.0.0













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

[0.3.0]: https://github.com/kami-lel/hupy/compare/v0.2.0...v0.3.0













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

[0.2.0]: https://github.com/kami-lel/hupy/releases/tag/v0.2.0













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
