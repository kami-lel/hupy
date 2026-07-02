# hupy CHANGELOG

[^format]















## [Unreleased]

### Added

- `pyproject.toml` — pip-installable `hupy` package using `setuptools.build_meta`
- `hupy/__init__.py` — package entry point
- `AGENTS.md` — agent behavioral instructions: setup commands, code style, testing, and PR rules
- `CONTEXT.md` — architecture overview, module responsibility table, and annotation marker tiers
- `.gitignore` — Python bytecode, build artifacts, venv dirs, and local agent override files
- `hupy/kamilog.py` — vendored logging module: custom levels (`ENTER`/`SKIP`/`SUCC`/`PASS`/`DONE`/`FAIL`), TTY-aware ANSI coloring, sliding-window diff-only message compression, comment banner (CB0~CB5) utilities, and a CLI with `comment_banner`/`cb` and `comment_banner_zero`/`cb0` subcommands
- `hupy/cli.py`, `hupy/__main__.py` — `hupy` CLI entrypoint and subcommand dispatch, wiring up `triage_tag_gating`/`ttg`
- `hupy/ttg/` package — Triage Tag Gating (TTG): `commit_type.py` classifies in-progress commits (Feature Finish, Version Release, other merge/commit types), `tt_detect.py` scans staged files for annotation markers, `tt_gating.py` blocks commits that introduce gated-tier tags on protected branches
- `examples/ttg/` — six runnable demo scripts covering fail, pass, and skip scenarios across Feature Finish and Version Release merges
- `tests/ttg/` — pytest suite for `commit_type`, `tt_detect`, and `tt_gating` (feature finish, version release, non-merge commit, regular merge, and error-path coverage), with a shared `prep_repo.py` scenario-fixture generator and a `tests/testee/default_repo.bundle` git bundle fixture

### Changed

- rewrote `README.md` with structured sections: features, tech stack, project layout, build and test, acknowledgments
- `pyproject.toml` — package metadata name corrected from `hupy` to `HUPy`; added `gitpython>=3.1` dependency

### Deprecated

### Removed

### Fixed

- build backend corrected from `setuptools.backends.legacy:build` to `setuptools.build_meta`

### Security

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.1.0...dev













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
