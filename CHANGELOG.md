# hupy CHANGELOG

[^format]

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

[unreleased]: https://github.com/kami-lel/hupy/compare/v2.0.0...dev













## [2.0.0] - 2026-07-18

### Added

- **`hupy uninstall`** — reverses `hupy init`, removing managed hook stubs and `.hupy.config.jsonc`; dry-run by default, `-f`/`--force` to delete
- **All seventeen git hook stages** now run under `hupy hook <stage>` (14 new), each with its own `hb` bracket section; Triage Tag Gating and Paper Trail also gate `pre-merge-commit`, since a conflict-free merge skips `pre-commit`
- **Paper Trail (PT)** — require at least one file matching a configured glob to change alongside a commit, aborting it otherwise; runs in `pre-commit`, `pre-merge-commit`, and `pre-rebase`; see `docs/pt_doc.md`
- **Demand-driven hook stubs** — a stage only gets a stub once its Hook Bracket is configured or it defines real hook logic; see `docs/stub_doc.md`
- **`hupy get`/`set`/`unset`/`info` accessor commands** — a generic key-based layer over `hupy-version`, `verbosity`, `skip-once`, `branch-type`, `grep-ver`, and `current-commit-type`
- **`--version`** flag on the top-level `hupy` command; `hupy set verbosity` now also accepts `-v`/`-q` offsets
- **HB command `timeout`** — an HB command can specify a `timeout` (seconds), failing the command on expiry per its `allow_failure`
- **Hook argument passthrough** — hook stubs forward git's own arguments into `hupy hook <stage>` and onward into HB bracket commands and each stage's own logic
- **Chain diagrams and demos** — `docs/chain_doc.md` gained Mermaid diagrams for every chain, and `examples/chain/` gained matching end-to-end demo scripts

### Changed

- **`hupy skip-once`/`so` → `hupy set skip-once`; `hupy set-verbosity`/`sv` → `hupy set verbosity`** — folded into the new accessor layer, each gaining a matching `hupy info <key>`
- `hupy init`'s hook-stub install now renders stubs in-process instead of copying bundled templates; flag renamed **`--copy-hooks` → `--install-hook-stubs`**
- `hupy verify` gains **`-u`/`--update-hook-stubs`** and **`-f`/`--force`** to sync stub drift, not just report it
- hook stubs now `exec` into `python` instead of forking it, keeping git as the direct parent process for reliable per-chain state tracking — re-run `hupy init --install-hook-stubs --force` (or `hupy verify -u -f`) on an already-installed repo
- HB bracket commands now run explicitly under `/bin/bash`, and every `hb` config section is optional, defaulting to empty
- logging: per-stage finish messages moved to `debug`; a single `done`-level message now prints once per chain instead of once per stage

### Removed

- bundled `hupy/assets/hook-stubs/*` template files — stubs are now rendered in-process
- `hupy skip-once`/`hupy set-verbosity` standalone subcommands — superseded by the accessor layer

### Fixed

- `hupy set skip-once` flags could leak past a chain that never runs `post-commit` (rebase-only, merge-only, or patch-apply-only chains); the reset now fires at whichever stage actually closes the chain

[2.0.0]: https://github.com/kami-lel/hupy/compare/v1.0.0...v2.0.0













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
