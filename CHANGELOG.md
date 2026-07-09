# hupy CHANGELOG

[^format]

## [Unreleased]

### Added

- **`init-create-config`** — new `hupy` subcommand that writes only the default `.hupy.config.json`, without touching hook stubs
- **`init-copy-hooks`** — new `hupy` subcommand that copies only the hook stub scripts into the repo's hooks directory, without writing a config file

### Changed

- `hupy init` now composes the two steps above; behavior is unchanged, but each step can be run standalone
- `init`'s positional repo argument renamed from `REPO_ROOT` to `REPO_PATH` (help text and `--help` output only; behavior unchanged)

### Deprecated

### Removed

### Fixed

- `examples/{pch,ttg}/*.bash` demo scripts rewritten as executable `.py` scripts; also fixes them actually running their hook (previously errored on a stray `prepend-commit-header`/`triage-tag-gating` CLI argument, and the demo repos never had a `.hupy.config.json` for the hook to load)

### Security

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.2.0...dev













## [0.2.0] - 2026-07-08

First version. **HUPy** is a ground-up Python reimplementation of the original bash [hooks-utility](https://github.com/kami-lel/hooks-utility), repackaging its git-hook commit-quality checks as an installable `hupy` command-line tool.

### Added

- **One-command setup** — `pip install` then `hupy init` drops the git hook stubs into a repository and writes a tracked `.hupy.config.json`; from then on the hooks run automatically on every commit
- **Triage Tag Gating** — a `pre-commit` check that blocks merges into protected branches when the staged changes still contain unfinished-work markers (`TODO`, `FIXME`, `HACK`, `BUG`), by severity tier: Loud when finishing a feature into `dev`, Loud and Steady when releasing to `main`
- **Prepend Commit Header** — a `prepare-commit-msg` step that automatically adds a descriptive header to Feature Finish and Version Release merge commits, stamping the project version on releases
- **Version detection** — reads the project's version from a file you configure, matched by a regular expression, for use in the release commit header
- **Commit-type detection** — recognizes the kind of in-progress commit (Feature Finish, Version Release, or ordinary) from git state, shared by both hooks
- **Configurable behavior** — a tracked `.hupy.config.json` controls log verbosity and the version lookup, so every clone of a repository behaves the same
- **Documentation and examples** — a README quick-start, per-feature guides under `docs/`, and runnable demo scripts under `examples/`

[0.2.0]: https://github.com/kami-lel/hooks-utility-py/releases/tag/v1.0.0













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
