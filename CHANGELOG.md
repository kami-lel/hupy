# hupy CHANGELOG

[^format]

## [Unreleased]

### Added

- **`init-create-config`** — new `hupy` subcommand that writes only the default `.hupy.config.json`, without touching hook stubs
- **`init-copy-hooks`** — new `hupy` subcommand that copies only the hook stub scripts into the repo's hooks directory, without writing a config file
- **six new merge types recognized** — `hupy.pch` now prepends commit headers for Sync Backport (`main`→`dev`), Catch Up (`dev`→feature), Hotfix Release (`hotfix/*`→`main`), Hotfix Backport (`hotfix/*`→`dev`), Release Cut (`release/*`→`main`), and Release Backport (`release/*`→`dev`), on top of the existing Feature Landing and Stable Release headers — 8 merge types total, each with its own header format and, where applicable, a version number
- **configurable branch names** — new `cbm` section in `.hupy.config.json` (`main_branch_name`, `dev_branch_name`, `hotfix_branch_prefix`, `release_branch_prefix`) replaces hardcoded `"main"`/`"dev"` branch matching
- **`hupy.ver_grep.grep_target_branch_version()`** and **`hupy.ver_grep.decide_version_update_type()`** — read a merge's target-branch version and classify a major/minor/patch version bump between source and target branches

### Changed

- `hupy init` now composes the two steps above; behavior is unchanged, but each step can be run standalone
- `init`'s positional repo argument renamed from `REPO_ROOT` to `REPO_PATH` (help text and `--help` output only; behavior unchanged)
- renamed generated commit-header terminology: **Feature Finish** → **Feature Landing**, **Version Release** → **Stable Release**, across code, docs, and generated commit headers
- restructured `hupy.commit_type` (flat module) into the `hupy.cbm` package (Commit/Branch/Merge), exposing `BranchType`, `CommitType`, `get_current_commit_type`, `get_source_branch`, `get_target_branch`
- restructured `hupy.ver_grep` (flat module, single `grep_repo_version()`) into a package split into `grep_source_branch_version()`/`grep_target_branch_version()`, each reading the branch tip via `git show` rather than the working tree
- consolidated `docs/pch_doc.md` into a new `docs/cbm_doc.md` guide covering Branch/Merge concepts, PCH headers, and `ver_grep`

### Deprecated

### Removed

- `docs/pch_doc.md` (folded into `docs/cbm_doc.md`)

### Fixed

- `examples/{pch,ttg}/*.bash` demo scripts rewritten as executable `.py` scripts; also fixes them actually running their hook (previously errored on a stray `prepend-commit-header`/`triage-tag-gating` CLI argument, and the demo repos never had a `.hupy.config.json` for the hook to load)

### Security

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.2.0...dev













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

[0.2.0]: https://github.com/kami-lel/hooks-utility-py/releases/tag/v1.0.0













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
