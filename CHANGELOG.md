# hupy CHANGELOG

[^format]















## [Unreleased]

### Added

- `hupy/config/model.py` — `HupyConfig` pydantic model, the schema for `.hupy.config.json`: `hupy_version` (defaulted from the installed package version) and `default_logger_verbosity` (base logging verbosity applied before `-v`/`-q` offsets)
- `hupy/config/load_config.py` — `load_config(repo_root)`: loads and validates `.hupy.config.json` against `HupyConfig`, exiting the process on a missing or malformed file
- `hupy/config/write_config.py` — `write_default_config(repo_root, force)`: writes `.hupy.config.json` generated from `HupyConfig` defaults
- `hupy/kamilog.py` — `set_logging_level_by_namespace(namespace, *, verbosity=0, logger=None, logger_name=None)`: applies a namespace's `-v`/`-q` counts as an offset atop a base `verbosity`
- `hupy/setup/cli_init.py` — `init` CLI subcommand: copies the two default hook stub scripts into the repo's actual hooks directory (`core.hooksPath` if configured, otherwise `.git/hooks/`; override with `--hooks-dir`) and writes a default `.hupy.config.json` at the repository root; `-f`/`--force` overrides an existing hook stub and/or config file
- `hupy/hook-stubs/` — default hook stub scripts packaged with `hupy` (`pre-commit`, `prepare-commit-msg`), each a thin wrapper invoking `python -m hupy <stage>`
- `hupy/config/.hupy.config.json` — default HUPy config template (JSON, tracks enabled features and their order per hook stage), packaged alongside the hook stubs
- `docs/hupy_config_doc.md` — placeholder doc for `.hupy.config.json`, linked from `README.md`
- `tests/setup/` — pytest suite for the `init` CLI subcommand and its helpers: hook-stub copy (fresh dir, unrelated pre-existing dir contents, per-file conflict abort/`-f` override), config-file write (fresh/conflict/`-f`), hooks-dir resolution (default `.git/hooks`, honoring configured `core.hooksPath`, relative and absolute), and end-to-end CLI coverage (`--hooks-dir` override beating a configured `core.hooksPath`, subdirectory resolution, non-atomic partial-write case, not-a-git-repo/nonexistent-path errors, `-v`/`-q` smoke checks); 25 tests
- `docs/ttg_doc.md`, `docs/pch_doc.md` — placeholder docs linked from `README.md`'s new Usage section
- `README.md` — Installation section (clone+`pip install` or `pip install` directly from GitHub, then `hupy init`, then see `docs/hupy_config_doc.md` for customizing behavior) and Usage section linking to the new `docs/` pages
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
- `hupy/ver_grep.py` — `grep_repo_version()`: regex-extracts a version string from a configured file (the pattern's first capturing group), returning `""` when `ver_grep` is unconfigured, or `raise SystemExit(1)` if the version file is missing or the pattern matches no line; own logger `VER_GREP_LOGGER_NAME` (`"HU.VerGrep"`)
- `hupy/config/model.py` — `_VerGrep` sub-model (`version_file: pathlib.Path`, `version_line_pattern: str`, both empty by default) nested under `HupyConfig.ver_grep`; `is_unconfigured()` reports whether either field is left at its empty default; a `model_validator(mode="after")` warns via the new `CONFIG_LOGGER_NAME` logger (`"HU.config-json"`, `hupy/config/__init__.py`) whenever an unconfigured instance is created
- `hupy/cli/` package — replaces the former flat `hupy/cli.py` and absorbs the former `hupy/setup/` package: `cli_main.py` (main parser + subcommand registration), `cli_init.py` (the `init` subcommand, moved from `hupy/setup/cli_init.py`, now also exporting `load_git_repo(repo_path)`), `cli_pre_commit.py` / `cli_prepare_commit_msg.py` (the `pre-commit`/`prepare-commit-msg` dispatch functions, split out of the old `cli.py`)
- `tests/ver_grep_test.py` — 11 tests for `grep_repo_version` (capture-group matching, first-match-wins, not-configured returns `""`, missing file / no matching line raise `SystemExit`)
- `tests/pch/pch-prepend_commit_header_version_release_test.py` — `TestVersionReleaseHeaderWithVersion`: 3 new tests covering the `"Version Release: <version>"` header when `ver_grep` resolves a version (semver and non-semver strings)
- `tests/cli/cli-cli_init_copy_hook_stubs_test.py` — `TestCopyHookStubsInterpreterPath`: 3 new tests asserting the `{{PYTHON}}` placeholder is replaced with `sys.executable` in installed stubs, the baked path is absolute, and the packaged templates still carry the placeholder
- `.hupy.config.json` — this repo now dogfoods `hupy` on itself (tracked config at the repo root, hook stubs installed into `.git/hooks/` via `hupy init`)

### Changed

- `hupy/cli.py` — `pre-commit`/`prepare-commit-msg` now load `.hupy.config.json` via `load_config()` and set the root logger level from `config.default_logger_verbosity` combined with `-v`/`-q` through `set_logging_level_by_namespace`, instead of a flags-only `set_logging_level_by_verbosity`
- `hupy/kamilog.py` — `set_logging_level_by_verbosity` now takes a plain verbosity int instead of an argparse namespace; namespace handling moved to the new `set_logging_level_by_namespace`
- `hupy/kamilog.py` — `getLogger()` now defaults to `datefmt=DATEFMT_TIME` (timestamps on) instead of `None`
- `hupy/commit_type.py`, `hupy/pch/prepend_commit_header.py`, `hupy/setup/cli_init.py`, `hupy/ttg/tt_gating.py` — disabled logger propagation (`logger.propagate = False`) so each module's own stdout/stderr handlers don't double-print through the root logger's handlers
- `hupy/setup/cli_init.py` — `init` now generates `.hupy.config.json` dynamically from `HupyConfig` defaults via `write_default_config()`, instead of copying the packaged static template
- `pyproject.toml` — added `pydantic>=2` dependency
- shortened the `pre-commit`/`prepare-commit-msg` stage log messages (`enter`/`succ`/`done`)
- **CLI subcommand tree flattened**: dropped the nested `start`/`<tool-name>`/`end` hook-stage subcommands in favor of `pre-commit`/`prepare-commit-msg` directly calling `perform_triage_tags_gating`/`prepend_commit_header`; `hupy/pch/parser.py`/`hupy/ttg/parser.py` were briefly renamed to `cli_pch.py`/`cli_ttg.py` before being folded into `hupy/cli.py` and removed
- rewrote `README.md` with structured sections: features, tech stack, project layout, build and test, acknowledgments
- `pyproject.toml` — package metadata name corrected from `hupy` to `HUPy`; added `gitpython>=3.1` dependency
- refactored `commit_type` from `hupy/ttg/commit_type.py` to top-level `hupy/commit_type.py`; it is a general commit-classification utility, not TTG-specific
- moved test file `tests/ttg/ttg-commit_type_test.py` to `tests/commit_type_test.py` to match module location
- `hupy/kamilog.py` — adjusted custom log levels to better distinguish hook/test state: `ENTER` 15, `SKIP` 16, `SUCC` 17, `PASS` 21, `DONE` 25, `FAIL` 45
- `hupy/cli.py` — separated TTG CLI parser into `hupy/ttg/parser.py`; PCH parser now lives in `hupy/pch/parser.py`; root parser retains subcommand dispatch
- **CLI subcommand tree restructured to mirror git hook stage names**: `triage_tag_gating`/`ttg` is now `pre-commit triage-tag-gating`, and `prepend_commit_header`/`pch` is now `prepare-commit-msg prepend-commit-header`; each stage also gained `start`/`end` stub subcommands (`pass  # TODO`) for future cross-cutting setup/teardown; the previous flat top-level `ttg`/`pch` aliases were dropped
- `examples/ttg/*.bash` and `examples/pch/*.bash` — updated CLI invocations to the new nested subcommand names
- `hupy/config/load_config.py` — renamed `load_config` to `load_hupy_config`; it now resolves the actual repo root via `load_git_repo(repo_path)` (so it works from any subdirectory, mirroring `init`) and caches the loaded/validated `HupyConfig` instance so the file is read from disk only once per process
- `hupy/pch/prepend_commit_header.py` — `_gen_version_release_header_content()` now calls `grep_repo_version()`; the header becomes `"Version Release: <version>"` when a version is available, falling back to plain `"Version Release"` otherwise
- `hupy/hook-stubs/{pre-commit,prepare-commit-msg}` — templates now invoke `"{{PYTHON}}" -m hupy <stage>` instead of `python -m hupy <stage> "$@"`; `_copy_hook_stubs` substitutes `{{PYTHON}}` with `sys.executable` (the interpreter running `hupy init`) when installing, so the hook always runs under the Python `hupy` is installed in — fixes hooks failing with `ModuleNotFoundError: No module named 'git'` when triggered without an activated venv on `PATH` (e.g. from an IDE's built-in git integration); note the installed stubs no longer forward `"$@"`, since `hupy`'s stage dispatch reads `.git/COMMIT_EDITMSG` directly rather than via argv
- `pyproject.toml` — dependency name corrected to canonical `GitPython>=3.1` casing (was `gitpython>=3.1`)
- `hupy/cli/cli_init.py` (formerly `hupy/setup/cli_init.py`) — extracted `load_git_repo(repo_path)`, reused by both `init` and `load_hupy_config`

### Deprecated

### Removed

- packaged static template `hupy/config/.hupy.config.json` and its `pyproject.toml` package-data entry — config is now generated dynamically from `HupyConfig` defaults
- `hupy/pch/cli_pch.py`, `hupy/ttg/cli_ttg.py` — folded into the flattened `hupy/cli.py`
- `tests/setup/setup-cli_init_write_default_config_test.py` — coverage folded into `setup-cli_init_init_cli_test.py`, asserting against `HupyConfig` defaults instead of the removed static template
- `hupy/setup/` package — folded into `hupy/cli/`; `SETUP_LOGGER_NAME` replaced by a plain `PROJ_LOGGER_NAME + ".init"` logger name defined inline in `cli_init.py`
- `hupy/cli.py` — split into `hupy/cli/cli_main.py`, `cli_pre_commit.py`, `cli_prepare_commit_msg.py`
- `tests/setup/` — moved to `tests/cli/`, files renamed to the `cli-cli_init_*` naming convention (mirrors the `hupy/cli/cli_init.py` move); `setup_helpers.py` renamed to `cli_helpers.py`

### Fixed

- build backend corrected from `setuptools.backends.legacy:build` to `setuptools.build_meta`
- `tests/commit_type_test.py` — corrected hardcoded branch name `"develop"` to `"dev"` to match module constant `DEV_BRANCH`; renamed test method `test_main_to_develop_boundary_is_other_merge` to `test_main_to_dev_boundary_is_other_merge`

### Security

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.1.0...dev













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
