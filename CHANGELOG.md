# hupy CHANGELOG

[^format]















## [Unreleased]

### Added

- `hupy/setup/` package — `init` CLI subcommand: copies the default hook scripts from `hupy/default-hupy-hooks/` into `REPO_ROOT/scripts/hupy-hooks/` (or `--hooks-dir`), then sets that path as the repo's `core.hooksPath`; supports `-f`/`--force` to override an existing hooks dir with a warning
- `hupy/default-hupy-hooks/` — default hook script templates packaged with `hupy` (`pre-commit.bash`, `prepare-commit-msg.bash`), bundled via `[tool.setuptools.package-data]` in `pyproject.toml`
- `docs/ttg_doc.md`, `docs/pch_doc.md` — placeholder docs linked from `README.md`'s new Usage section
- `README.md` — Installation section (clone+`pip install` or `pip install` directly from GitHub, then `hupy init`, then customize the copied hook scripts) and Usage section linking to the new `docs/` pages
- `hupy/pch/` package — Prepend Commit Header (PCH): `prepend_commit_header.py` rewrites in-progress commit messages to prepend a header line for Feature Finish and Version Release merges, `parser.py` wires up the `prepend_commit_header`/`pch` CLI subcommand
- `examples/pch/` — four runnable demo scripts: Feature Finish and Version Release passes, plus skipped scenarios (non-merge commit, irrelevant merge)
- `tests/pch/` — comprehensive pytest suite for `prepend_commit_header()`; covers Feature Finish and Version Release header selection, message formatting edge cases (comment regrouping, Unicode round-trip, empty messages), error paths (missing `COMMIT_EDITMSG`, atomic write failures), and skip paths (non-merge, regular merge); 15 tests
- `hupy/ttg/parser.py` — refactored CLI parser from `hupy/cli.py` into a separate module for modularity
- `pyproject.toml` — pip-installable `hupy` package using `setuptools.build_meta`
- `hupy/__init__.py` — package entry point
- `AGENTS.md` — agent behavioral instructions: setup commands, code style, testing, and PR rules
- `CONTEXT.md` — architecture overview, module responsibility table, and annotation marker tiers
- `.gitignore` — Python bytecode, build artifacts, venv dirs, and local agent override files
- `hupy/kamilog.py` — vendored logging module: custom levels (`ENTER`/`SKIP`/`SUCC`/`PASS`/`DONE`/`FAIL`), TTY-aware ANSI coloring, sliding-window diff-only message compression, comment banner (CB0~CB5) utilities, and a CLI with `comment_banner`/`cb` and `comment_banner_zero`/`cb0` subcommands
- `hupy/commit_type.py` — classifies an in-progress git commit by type (Feature Finish, Version Release, other merge/commit), inspecting git state files (`MERGE_HEAD`, branches, remote refs)
- `hupy/cli.py`, `hupy/__main__.py` — `hupy` CLI entrypoint and subcommand dispatch, wiring up `triage_tag_gating`/`ttg` and `prepend_commit_header`/`pch`
- `hupy/ttg/` package — Triage Tag Gating (TTG): `tt_detect.py` scans staged files for annotation markers, `tt_gating.py` blocks commits that introduce gated-tier tags on protected branches
- `examples/ttg/` — six runnable demo scripts covering fail, pass, and skip scenarios across Feature Finish and Version Release merges
- `tests/ttg/` — pytest suite for `commit_type`, `tt_detect`, and `tt_gating` (feature finish, version release, non-merge commit, regular merge, and error-path coverage), with a shared `prep_repo.py` scenario-fixture generator and a `tests/testee/default_repo.bundle` git bundle fixture

### Changed

- rewrote `README.md` with structured sections: features, tech stack, project layout, build and test, acknowledgments
- `pyproject.toml` — package metadata name corrected from `hupy` to `HUPy`; added `gitpython>=3.1` dependency
- refactored `commit_type` from `hupy/ttg/commit_type.py` to top-level `hupy/commit_type.py`; it is a general commit-classification utility, not TTG-specific
- moved test file `tests/ttg/ttg-commit_type_test.py` to `tests/commit_type_test.py` to match module location
- `hupy/kamilog.py` — adjusted custom log levels to better distinguish hook/test state: `ENTER` 15, `SKIP` 16, `SUCC` 17, `PASS` 21, `DONE` 25, `FAIL` 45
- `hupy/cli.py` — separated TTG CLI parser into `hupy/ttg/parser.py`; PCH parser now lives in `hupy/pch/parser.py`; root parser retains subcommand dispatch
- **CLI subcommand tree restructured to mirror git hook stage names**: `triage_tag_gating`/`ttg` is now `pre-commit triage-tag-gating`, and `prepend_commit_header`/`pch` is now `prepare-commit-msg prepend-commit-header`; each stage also gained `start`/`end` stub subcommands (`pass  # TODO`) for future cross-cutting setup/teardown; the previous flat top-level `ttg`/`pch` aliases were dropped
- `examples/ttg/*.bash` and `examples/pch/*.bash` — updated CLI invocations to the new nested subcommand names

### Deprecated

### Removed

### Fixed

- build backend corrected from `setuptools.backends.legacy:build` to `setuptools.build_meta`
- `tests/commit_type_test.py` — corrected hardcoded branch name `"develop"` to `"dev"` to match module constant `DEV_BRANCH`; renamed test method `test_main_to_develop_boundary_is_other_merge` to `test_main_to_dev_boundary_is_other_merge`

### Security

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.1.0...dev













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
