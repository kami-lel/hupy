# hupy CONTEXT

*Last updated: 2026-07-10 — restructured commit/branch/merge detection and version grepping into two packages, and expanded PCH to cover every CBM merge type: `hupy/commit_type.py` (flat module) became `hupy/cbm/` (Commit/Branch/Merge), adding a `BranchType(Enum)` (`FEATURE`/`DEV`/`MAIN`/`HOTFIX`/`RELEASE`/`USER`) classified by `BranchType.from_name(branch_name, repo)` against a new config-driven `cbm` section (`main_branch_name`/`dev_branch_name`/`hotfix_branch_prefix`/`release_branch_prefix` in `.hupy.config.json`, replacing the old hardcoded `MAIN_BRANCH`/`DEV_BRANCH` constants), and widening `CommitType.decide_commit_type(source, target)` from 2 recognized merge types to 8 (`FEATURE_LANDING`, `STABLE_RELEASE`, `SYNC_BACKPORT`, `CATCH_UP`, `HOTFIX_RELEASE`, `HOTFIX_BACKPORT`, `RELEASE_CUT`, `RELEASE_BACKPORT`, plus `OTHER_MERGE`); `hupy/ver_grep.py` (flat module, single `grep_repo_version()`) became `hupy/ver_grep/`, split into `grep_source_branch_version()`/`grep_target_branch_version()` (each resolving its branch's tip via `repo.git.show(...)` rather than the working tree, since mid-merge the working tree only ever holds the target branch's content) plus a new `decide_version_update_type(source_version, target_version)` major/minor/patch bump classifier (not yet wired into `pch`); `config.HupyConfig` renamed to `HupyConfigFile` (`config/model.py` → `config/hupy_config_file.py`), gaining the nested `_Cbm` model above, and `load_hupy_config` now takes an already-open `git.Repo` (not a path) — called that way from both `cbm.branch_type` and `ver_grep.branch_version`; `pch.prepend_commit_header` grew a `_HEADER_GENERATORS` dict covering all 8 merge types (previously only `FEATURE_LANDING`/`STABLE_RELEASE`), each producing its own header format, several version-stamped via `grep_source_branch_version()`; renamed **Feature Finish**/**Version Release** terminology to **Feature Landing**/**Stable Release** throughout; folded `docs/pch_doc.md` into a new consolidated `docs/cbm_doc.md` (Branch/Merge concept tables + Mermaid graphs, `cbm`/`pch`/`ver_grep` module docs); added `examples/pch/{sync-backport,catch-up,hotfix-release,hotfix-backport,release-cut,release-backport}-demo.py` and reorganized test suites into `tests/cbm/` (+ `tests/cbm/grct/` for `get_current_commit_type`/`get_source_branch`/`get_target_branch`) and `tests/vg/`, replacing the old flat `tests/commit_type_test.py`/`tests/ver_grep_test.py`. **Known gap**: `examples/pch/hotfix-backport-demo.py`'s docstring/expected output still says "skip (merge type not yet handled by PCH)" — stale, since `HOTFIX_BACKPORT` is now in `_HEADER_GENERATORS`; likewise `tests/fixtures/prep_repo.py`'s `DEMO_BUCKETS` comment ("CBM merge types PCH does not yet handle") no longer matches `pch`'s actual coverage. `docs/hupy_config_doc.md` doesn't yet document the new `cbm` config section, and `docs/cbm_doc.md`'s `get_current_commit_type` example still shows the old `repo_path`-string signature instead of the current `git.Repo` one — both left for a docs-focused pass. (previous round: deduplicated repeated aux fx across `examples/pch/*-demo.py` and `examples/ttg/*-demo.py`: added `examples/pch/__init__.py` (`prepare_demo_repo_by_scenario`/`prepare_demo_repo_by_bucket`/`run_pch`) and `examples/ttg/__init__.py` (`prepare_demo_repo`/`run_ttg`, the latter calling `perform_triage_tags_gating` directly rather than the full `pre-commit` CLI), imported back into each sibling demo script via `from __init__ import ...`; also dropped the redundant `ttg-` filename prefix from `examples/ttg/*-demo.py` and restructured their printed output to match `examples/pch/*-demo.py`'s `print out`/`=`-banner style (also dropping the middle `-v` verbosity block to match). No `hupy/` source changes. (previous round: reorganized test/demo fixtures: `tests/testee/` renamed to `tests/fixtures/` (shared-by-all fixtures: bundle + `prep_repo.py`, moved out of `tests/ttg/`); `tests/testee/ttg/` fixture content moved to `tests/ttg/fixtures/` (ttg-domain-specific, not shared); added a root `tests/conftest.py` with the `repo_dir` fixture, deduplicated out of `tests/{pch,ttg,cli}/conftest.py`; `prep_repo.py` gained `prepare_demo_repo`/`DEMO_BUCKETS` for the 6 CBM merge types PCH doesn't yet handle, replacing bespoke git-branching code duplicated across those `examples/pch/*-demo.py` scripts; introduced `examples/hooks/` for bash demos that drive the real `hupy <stage>` CLI end-to-end (as opposed to `examples/{pch,ttg}/*.py`, which call internal functions directly) — moved `prepare-commit-msg-demo.sh` there (now shells out to `prep_repo.py --scenario ...` instead of hand-rolling the demo repo in bash) and added `pre-commit-demo.sh` (Feature Landing, steady+quiet TT only, expects PASS) plus a placeholder `all-hooks-demo.sh` to run both in sequence. No `hupy/` source changes. (previous round: split `init`'s two steps out into standalone subcommands: `_copy_hook_stubs`/`_resolve_hooks_dir` (plus `_HOOK_STUBS_DIR`/`_PYTHON_PLACEHOLDER`) moved out of `cli_init.py` into a new `cli_ich.py` (`init-copy-hooks` subcommand), and a new `cli_icc.py` wraps `write_default_config` as `init-create-config`; `init` (`cli_init.py`) now composes both via a function-local import of `cli_ich`'s two helpers (module-level would cycle, since `cli_ich.py` imports `INIT_LOGGER_NAME`/`REPO_PATH_HELP`/`load_git_repo` back from `cli_init.py`); `cli_init.py` gained exported `INIT_LOGGER_NAME`/`REPO_PATH_HELP` constants for the new modules to share, and its positional repo argument was renamed `repo_root`/`REPO_ROOT` → `repo_path`/`REPO_PATH` (all three subcommands now use this name). Registered both new subcommands in `cli_main.py`. Left unfixed in this round: `tests/cli/`'s three existing test files still import the moved helpers from `hupy.cli.cli_init` and fail to collect; no test file yet for `cli_icc`/`cli_ich`'s own wiring. (previous round: cut the **v1.0.0** release (first release; bumped `pyproject.toml`/`.hupy.config.json` to 1.0.0, rewrote `CHANGELOG.md` into a high-level release note framing HUPy as a Python reimplementation of the bash [hooks-utility](https://github.com/kami-lel/hooks-utility)) and, in the same round, fleshed out the three `docs/` pages (`ttg_doc.md`, `pch_doc.md`, `hupy_config_doc.md`) from placeholders into user-facing feature/config references, added a Usage section with a Mermaid hook-flow diagram to `README.md`, and configured this repo's own `.hupy.config.json` `ver_grep` to read the version from `pyproject.toml`; CONTEXT changes were the Status line (now released v1.0.0) and the Package Layout comments for those docs (no architecture change). (previous round: folded the `setup` package into a new `cli` package (`hupy/setup/cli_init.py` → `hupy/cli/cli_init.py`, gaining an exported `load_git_repo(repo_path)`), and split the former flat `hupy/cli.py` into `cli/cli_main.py` (parser + registration) plus `cli/cli_pre_commit.py`/`cli/cli_prepare_commit_msg.py` (stage dispatch); added a `ver_grep` module (`grep_repo_version()`, regex-extracts a version string from a configured file) and a nested `_VerGrep` config sub-model (`ver_grep.version_file`/`version_line_pattern`, `is_unconfigured()`, warn-on-create validator), wired into `pch`'s Stable Release header (`"Stable Release: <version>"` when available); `config.load_config` renamed to `load_hupy_config`, now resolving the repo root via `load_git_repo` and caching the validated `HupyConfig` per process; hook stub templates switched from a bare `python -m hupy <stage> "$@"` to a `{{PYTHON}}` placeholder substituted with `sys.executable` at `init` time, fixing hooks failing under environments (e.g. an IDE's git integration) that don't source the project venv onto `PATH`. Updated the module table, Hook Integration Model, `cli`/`config` Module Details (folding the old `setup` section into `cli`), added a `ver_grep` Module Details section, Package Layout, and Testing Infrastructure accordingly (previous round: introduced a `config` package (`HupyConfig` pydantic model, `load_config`, `write_default_config`) so `.hupy.config.json` is generated from model defaults instead of a static template, and wired its `default_logger_verbosity` field into `cli.py`'s `pre-commit`/`prepare-commit-msg` dispatch via a new `kamilog.set_logging_level_by_namespace(namespace, *, verbosity=0, ...)`, while `set_logging_level_by_verbosity` was narrowed to take a plain int; also disabled logger propagation on `commit_type`, `pch.prepend_commit_header`, `setup.cli_init`, and `ttg.tt_gating`, and flattened the CLI subcommand tree; before that, implemented the reversed Hook Integration Model in code — `setup/parser.py` renamed to `setup/cli_init.py`, hook stubs and config copied into the repo from packaged templates, `tests/setup/` rewritten to match, 25 tests; before that, documented this design change ahead of implementation; before that, `setup`/`init` implemented the prior `scripts/hupy-hooks/`/`core.hooksPath` design; before that, re-audited source tree against docs and restructured `cli`'s subcommand tree to mirror git hook stages)))))*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Status: **v0.2.0 released, unreleased work in progress** — `cbm` (Commit/Branch/Merge, formerly `commit_type`), `kamilog`, `cli` (including `init`), `config`, `pch` (Prepend Commit Header, now covering 8 merge types), `ver_grep`, and the `ttg` package (Triage Tag Gating) are implemented; `branch_protection` and `ensure_file_edited` are not yet started.

Package: `HUPy` (import name `hupy`) · build: `setuptools` · install: `pip install -e ".[dev]"` · dependencies: `GitPython>=3.1`, `pydantic>=2`

## Architecture

Each utility is a standalone module in the `hupy/` package, callable independently from any git hook script. No cross-module dependencies are assumed, except within the `ttg` package itself and `pch`'s/`ttg`'s use of `cbm`, and `cbm`'s/`ver_grep`'s use of `config`.

| Module | Status | Responsibility |
|---|---|---|
| `cli` | **implemented** | CLI entrypoint, argument parsing/dispatch (`cli_main.py`); `init` subcommand and Git repo loading (`cli_init.py`); `pre-commit`/`prepare-commit-msg` stage runners (`cli_pre_commit.py`, `cli_prepare_commit_msg.py`) |
| `cbm` | **implemented** | Commit/Branch/Merge — classify a branch name as a `BranchType` and an in-progress commit as a `CommitType` enum member (formerly the flat `commit_type` module) |
| `config` | **implemented** | `HupyConfigFile` pydantic schema for `.hupy.config.json` (including the nested `ver_grep` and `cbm` sections), cached loading resolved against an already-open `git.Repo`, and default-writing helpers |
| `kamilog` | **implemented** | customized logging with extra levels, ANSI color, diff compression, comment banners, and a standalone CLI |
| `pch` | **implemented** | prepend header lines to in-progress commit messages for all 8 `cbm` merge types; several append a version number via `ver_grep` when configured |
| `ver_grep` | **implemented** | extract a merge's source/target branch version string by regex-matching a line in a configured version file, read at that branch's git tip; also classifies major/minor/patch version bumps |
| `ttg.tt_detect` | **implemented** | scan staged diffs for triage tag annotation markers, tiered by loudness |
| `ttg.tt_gating` | **implemented** | gate commits by triage tag presence on protected branches |
| `ensure_file_edited` | not yet implemented | require specific files or line ranges to be modified in the commit; a bash-era utility being ported, per the `# todo reimplement ensure file modified` marker in `hupy/__init__.py` |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **stateless** — relies on git state and file diffs; no persistent storage
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

**Decision**: `hupy init` sets a repo up with two artifacts:

1. A tracked, dot-prefixed config file at the repo root, **`.hupy.config.json`** (JSON) — the config surface: which features (`ttg`, `pch`, and future ones) are enabled, and in what order they run per hook stage. Being tracked/committed, it's reviewable and shared across clones the same way any other project file is. Default content is generated from `HupyConfigFile` defaults (see `config` in Module Details), not copied from a static template.
2. Two thin stub scripts copied into the repo's actual hooks directory: `pre-commit` and `prepare-commit-msg`, sourced from the packaged `hupy/hook-stubs/`. Each stub does nothing but invoke the corresponding CLI stage group — `"<python>" -m hupy pre-commit` / `"<python>" -m hupy prepare-commit-msg` — which then reads `.hupy.config.json` via `load_hupy_config(repo)`; today `default_logger_verbosity`, `ver_grep`, and `cbm` are consumed (feature enable/order fields aren't in `HupyConfigFile` yet — see `cli` and `config` in Module Details).

- **Config surface = `.hupy.config.json`, not the hook script.** This reverses an earlier "config surface = the script itself" decision (see *Prior rejections* below). The hook stub is a fixed, content-free trampoline; enabling/disabling a feature and controlling its order both become a JSON edit, not a bash edit.
- **Dot-prefixed naming (`.hupy.config.json`, not `hupy.config.json`)**: chosen by analogy to the Python ecosystem's single-purpose tool-config dotfiles (`.flake8`, `.pylintrc`, `.coveragerc`, `.isort.cfg`), and specifically to `.pre-commit-config.yaml` — the closest sibling in the ecosystem (same domain: tracked, root-level git-hook-orchestration config) and the exact framework rejected below as a dependency. Visible top-level docs in this repo (`AGENTS.md`, `CHANGELOG.md`, `CONTEXT.md`) were considered as a naming precedent and rejected — those are human-authored prose meant to be read, not tool-consumed config.
- **Hooks directory is resolved, not fixed to `.git/hooks/`.** `hupy.cli.cli_init._resolve_hooks_dir(repo)` reads `core.hooksPath` via GitPython's `config_reader()` and joins it onto `repo.working_tree_dir` if set (resolving relative to the repo root; an absolute configured path is used as-is since `pathlib` path-joining drops the left side when the right side is absolute), otherwise falls back to `pathlib.Path(repo.git_dir) / "hooks"`. `--hooks-dir` overrides this resolution entirely. `init` itself never writes `core.hooksPath` — an earlier design's redirection-at-a-tracked-directory approach (see *Prior rejections*) is unnecessary now that the hook scripts carry no meaningful content of their own; the reviewable content lives in `.hupy.config.json` instead.
- **Per-file conflict checks, not directory-level.** `_copy_hook_stubs` only checks whether each individual target filename (`pre-commit`, `prepare-commit-msg`) already exists — not whether the hooks directory itself exists. `.git/hooks/` always exists after `git init` (populated with git's own `*.sample` files), so a directory-existence check would force `-f` on every default-path run; per-file checks let a fresh repo's first `init` succeed without `-f` while still protecting a real pre-existing hook.
- **Calls the CLI, not internal functions.** The stub invokes `<python> -m hupy <subcommand>` rather than importing `hupy.ttg`/`hupy.pch` Python functions directly, because the CLI subcommands are `hupy`'s stable, documented public interface.
- **Interpreter path is baked in at install time, not resolved from `PATH`.** The packaged stub templates carry a `"{{PYTHON}}"` placeholder; `_copy_hook_stubs` substitutes it with `sys.executable` (the interpreter running `hupy init`) before writing each stub. A bare `python`/`python3` on `PATH` is unreliable for a git hook: hooks run in whatever environment invokes `git commit` — an IDE's built-in git integration, for instance, does not source the project's venv onto `PATH` — so a bare interpreter name can resolve to a system Python lacking both `hupy` and its dependencies (`ModuleNotFoundError: No module named 'git'`). Baking in the absolute path makes the hook work regardless of which client or shell state triggers the commit. A consequence: re-running `hupy init --force` is required after moving/recreating the virtualenv the package is installed in, since the old absolute path would otherwise go stale.
- **`-f`/`--force` gates the hook stubs and the config file independently** — `_copy_hook_stubs` and `write_default_config` each perform their own existence/`force` check, so (e.g.) a pre-existing config with fresh hooks still aborts on the config step even though the hooks were already written; `init` is not atomic across the two artifacts (mirrors the non-atomicity of the prior design between copying scripts and configuring `core.hooksPath`).
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

**`BranchType(Enum)`** — `FEATURE` | `DEV` | `MAIN` | `HOTFIX` | `RELEASE` | `USER`. `BranchType.from_name(branch_name, repo)` classifies against the `cbm` section of `.hupy.config.json` (via `load_hupy_config(repo).cbm`), checked in order: `dev_branch_name` → `DEV`, `main_branch_name` → `MAIN`, `f"{hotfix_branch_prefix}/"` prefix → `HOTFIX`, `f"{release_branch_prefix}/"` prefix → `RELEASE`, any other `/` in the name → `USER`, otherwise → `FEATURE`. Branch names are no longer hardcoded (previously module-level `MAIN_BRANCH = "main"`/`DEV_BRANCH = "dev"` constants).

**`CommitType(Flag)`** — two-level bitmask hierarchy:

- level 1: `MERGE` | `OTHER_COMMIT`
- level 2 (under `MERGE`): `FEATURE_LANDING` | `STABLE_RELEASE` | `SYNC_BACKPORT` | `CATCH_UP` | `HOTFIX_RELEASE` | `HOTFIX_BACKPORT` | `RELEASE_CUT` | `RELEASE_BACKPORT` | `OTHER_MERGE`

`CommitType.decide_commit_type(source, target)` maps a `(BranchType, BranchType)` pair via `_MERGE_TYPE_BY_BRANCH_PAIR`: `(FEATURE, DEV)`→`FEATURE_LANDING`, `(DEV, MAIN)`→`STABLE_RELEASE`, `(MAIN, DEV)`→`SYNC_BACKPORT`, `(DEV, FEATURE)`→`CATCH_UP`, `(HOTFIX, MAIN)`→`HOTFIX_RELEASE`, `(HOTFIX, DEV)`→`HOTFIX_BACKPORT`, `(RELEASE, MAIN)`→`RELEASE_CUT`, `(RELEASE, DEV)`→`RELEASE_BACKPORT`; any other pair → `OTHER_MERGE`. See `docs/cbm_doc.md` for the full Branch/Merge Type concept tables and Mermaid graphs.

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

**Public API**: `prepend_commit_header(repo)` — detect current commit type via `cbm.get_current_commit_type(repo)`, then prepend an appropriate header and rewrite `.git/COMMIT_EDITMSG`

Header generation logic — a `_HEADER_GENERATORS` dict keyed by `CommitType`, one generator per merge type:

| `CommitType` | Header format |
|---|---|
| `FEATURE_LANDING` | `"Feature Landing: <source-branch-name>"` (via `get_source_branch(repo)`) |
| `STABLE_RELEASE` | `"Stable Release: <version>"`, or plain `"Stable Release"` if `grep_source_branch_version()` returns `""` |
| `SYNC_BACKPORT` | `"Sync Backport from: <version>"` or plain `"Sync Backport"` |
| `CATCH_UP` | plain `"Catch Up"` (no version lookup) |
| `HOTFIX_RELEASE` | `"Hotfix Release: <version>"` or plain `"Hotfix Release"` |
| `HOTFIX_BACKPORT` | `"Hotfix Backport from: <version>"` or plain `"Hotfix Backport"` |
| `RELEASE_CUT` | `"Release Cut: <version>"` or plain `"Release Cut"` |
| `RELEASE_BACKPORT` | `"Release Backport from: <version>"` or plain `"Release Backport"` |

`OTHER_COMMIT`/`OTHER_MERGE` (not in `_HEADER_GENERATORS`) → file left untouched, no exception.

The rewrite separates comment lines (starting with `#`) from content, placing all comments after the content block to preserve git's template comments. Non-destructive on failure: if the atomic write via `os.replace()` fails, the original file is untouched and the temporary file is cleaned up.

**Known gap**: `examples/pch/hotfix-backport-demo.py`'s docstring/expected output still says "skip (merge type not yet handled by PCH)", left over from before `HOTFIX_BACKPORT` gained a generator above — it's stale relative to the current code and should be updated to expect a header. `tests/fixtures/prep_repo.py`'s `DEMO_BUCKETS` comment has the same stale claim.

README flags a planned scenario not yet covered by `examples/pch/`/`tests/pch/`: keeping a feature branch up to date by merging `dev` back *into* it (as opposed to the Feature Landing direction, feature → `dev`) — this is now `CATCH_UP` above and has a demo/bucket, but no dedicated `tests/pch/` assertions yet.

### `config`

Config schema, loading, and default-writing for `.hupy.config.json`.

**Public API**: `CONFIG_FILENAME` (`hupy/config/__init__.py`, `= ".hupy.config.json"`) · `CONFIG_LOGGER_NAME` (`= "HU.config-file"`) · `HupyConfigFile` (`hupy_config_file.py`, renamed from `HupyConfig`/`model.py`) · `load_hupy_config(repo)` (`load_config.py`) · `write_default_config(repo_root, force)` (`write_config.py`)

- **`HupyConfigFile(BaseModel)`** — `hupy_version: str` (defaulted via `importlib.metadata.version("HUPy")`), `default_logger_verbosity: int = 1` (base verbosity `cli` passes into `set_logging_level_by_namespace` before `-v`/`-q` offsets apply), `ver_grep: _VerGrep` (defaulted via `Field(default_factory=_VerGrep)`), and `cbm: _Cbm` — a new nested section for branch-name config
- **`_VerGrep(BaseModel)`** — `version_file: pathlib.Path` and `version_line_pattern: str`, both empty by default (see `ver_grep` in Module Details for how these are consumed). `is_unconfigured()` returns `True` when `version_file` is empty/`"."` (`pathlib.Path("")` normalizes to `.`) or `version_line_pattern` is blank. A `model_validator(mode="after")` calls `is_unconfigured()` on every instance creation and, if `True`, logs a `logger.warning(...)` via `CONFIG_LOGGER_NAME` rather than raising — an unconfigured `ver_grep` is a valid, non-fatal state (e.g. the default config `hupy init` writes)
- **`_Cbm(BaseModel)`** — `main_branch_name: str = "main"`, `dev_branch_name: str = "dev"`, `hotfix_branch_prefix: str = "hotfix"`, `release_branch_prefix: str = "release"` (all `Field(..., min_length=1)`); consumed by `cbm.branch_type.BranchType.from_name` (see `cbm` in Module Details) — not yet documented in `docs/hupy_config_doc.md`
- **`load_hupy_config(repo)`** — **now takes an already-open `git.Repo`**, not a path (previously resolved the repo itself via `hupy.cli.cli_init.load_git_repo(repo_path)`; that resolution is now the caller's job). Reads and `HupyConfigFile.model_validate_json()`-validates `pathlib.Path(repo.working_tree_dir) / CONFIG_FILENAME`; on `FileNotFoundError` or `pydantic.ValidationError`, logs and `raise SystemExit(1) from e` rather than propagating the exception. Caches the validated instance in a module-level `_config_cache` so the file is read from disk only once per process — repeated calls (e.g. from `cli_pre_commit`/`cli_prepare_commit_msg` dispatch, `cbm.branch_type`, and `ver_grep.branch_version`) return the same instance
- **`write_default_config(repo_root, force)`** — same existence/`force` conflict pattern as `_copy_hook_stubs` (see `cli` below), writing `HupyConfigFile().model_dump_json(indent=2) + "\n"`; used by `hupy init`, not by `load_hupy_config`
- no dedicated test suite yet (`# todo unit test for configs` in `hupy/config/__init__.py`); `write_default_config` is currently only exercised indirectly through `tests/cli/cli-cli_init_init_cli_test.py`

### `ver_grep`

Reads a merge's source/target branch version string by regex-matching a line in a configured version file, resolved at that branch's git tip (not the working tree — mid-merge, the working tree only ever holds the target branch's, possibly conflicted, content); consumed by `pch` to append version numbers to several merge-type commit headers. Formerly a flat module exposing a single `grep_repo_version()`, now a package split by branch role, plus a version-bump classifier.

**Public API** (`hupy/ver_grep/__init__.py`): `grep_source_branch_version()` · `grep_target_branch_version()` · `decide_version_update_type(source_version, target_version)`

- **`grep_source_branch_version()` / `grep_target_branch_version()`** (`branch_version.py`) — both take no arguments; each resolves `repo = git.Repo(os.getcwd(), search_parent_directories=True)`, loads `ver_grep` config via `load_hupy_config(repo)`, resolves the relevant branch name via `cbm.get_source_branch(repo)`/`get_target_branch(repo)`, then reads that branch's version file at its tip via `repo.git.show(f"{ref}:{version_file}")` and `re.search(pattern, line)`s each line in order, returning the first capturing-group match. Flow, in order:
  1. if `config.ver_grep.is_unconfigured()` → `logger.warning(...)` and return `""` — a non-fatal, expected state, not an error
  2. if `version_file` doesn't exist at that branch's tip → `logger.error(...)` + `raise SystemExit(1)`
  3. no line matches the pattern → `logger.error(...)` + `raise SystemExit(1)`
- **`decide_version_update_type(source_version, target_version)`** (`version_bump.py`) — parses `major.minor.patch` cores via `^(\d+)\.(\d+)\.(\d+)` (ignoring any pre-release/build suffix), returns `"x"` for a major bump, `"y"` for minor, `"z"` for patch, or `""` if unparsable or not actually a bump (equal or lower) — **not yet wired into `pch`**, available for future use (e.g. picking a header word by bump size)
- Own logger `VER_GREP_LOGGER_NAME` (`"HU.VerGrep"`), propagation disabled.

### `ttg.tt_detect`

Scans staged git diffs for triage tag annotation markers.

**Public API**: `detect_triage_tags_in_staged_file(file_path, repo_root=None)` → `list[(TriageTagType, str)]` — runs `git diff --cached -- file_path`, and for every added (`+`) line, records the first matching tag and the line text

**`TriageTagType(Flag)`** — 12 members across 3 tiers × 4 kinds (`TODO`/`FIXME`/`HACK`/`BUG`), each matched case-sensitively (`TODO` loud, `Todo` steady, `todo` quiet); composite groups `LOUDS`/`STEADYS`/`QUIETS` (by tier) and `TODOS`/`FIXMES`/`HACKS`/`BUGS` (by kind) are pre-defined flag combinations

- `TriageTagType.find_first_in_line(line)` — first tag match in a line, or `None`
- `TriageTagType.filter_by_group(tags, group)` — keep only tags belonging to a group (e.g. `LOUDS`, `TODOS | STEADYS`)

Detection is a plain regex word-boundary match on the whole added line — it does not check whether the match sits inside a comment for the file's language (`# todo detect TT with respect of code comment by file type`), so a tag appearing in a string literal or non-comment context would still register.

### `ttg.tt_gating`

Triage tag (TT) gating — blocks commits that introduce annotation markers on protected branches.

**Public API**: `perform_triage_tags_gating(repo)` — detect current commit type via `cbm.get_current_commit_type(repo)`, then gate on the tag tiers appropriate to that merge type

Gating policy by commit type:

- `FEATURE_LANDING` → gates `LOUDS`
- `STABLE_RELEASE` → gates `LOUDS | STEADYS`
- anything else → skipped, no gating

On a gated match, `_perform_triage_tags_by_filtering_group` builds a report (file name banners via `kamilog.gen_comment_banner_centered`, `"-"` fill) and raises `SystemExit(1)`. The reported lines are plain text — no highlighting on the matched tag itself yet (`# todo print gated TT in colored highlighting`).

`tt_gating` and `tt_detect` share one logger, `TTG_LOGGER_NAME` (`"HU.TTG"`), defined in `hupy/ttg/__init__.py` **before** the `from .tt_gating import ...` line — `tt_gating` imports `TTG_LOGGER_NAME` back from the package `__init__`, so the definition must precede the import or it fails with a circular-import `ImportError`. `cbm` keeps its own separate logger, `CBM_LOGGER_NAME` (`"HU.CBM"`).

### `cli`

Argument parser and entrypoint for the `hupy` command-line tool; a package (`hupy/cli/`, formerly a flat `hupy/cli.py`) split by subcommand.

**Public API**: `cli_parser` (ArgumentParser) · `cli_subparser` (subparsers action) — both in `cli_main.py` · `register_cli_init_parser`/`load_git_repo`/`INIT_LOGGER_NAME`/`REPO_PATH_HELP` (`cli_init.py`) · `register_cli_icc_parser` (`cli_icc.py`) · `register_cli_ich_parser`/`_copy_hook_stubs`/`_resolve_hooks_dir` (`cli_ich.py`) · `register_cli_pre_commit_parser` (`cli_pre_commit.py`) · `register_cli_prepare_commit_msg_parser` (`cli_prepare_commit_msg.py`)

The CLI has five top-level subcommands, mirroring the hook stages and setup:

```
hupy init
hupy init-create-config
hupy init-copy-hooks
hupy pre-commit
hupy prepare-commit-msg
```

- **`cli_main.py`** — main parser and dispatch, unchanged in shape from the old `cli.py`: `prog="hupy"` (a literal string, not `__package__`, since this module now lives *inside* the `hupy.cli` package and `__package__` would otherwise resolve to `"hupy.cli"`), `description=__doc__`; imports each subcommand module's `register_*_parser` and calls them in turn against `cli_subparser`
- **`init`** — implemented in `cli_init.py` (moved from the former `hupy/setup/cli_init.py`); onboards a repository onto `hupy` by writing the two hook stubs and a default `.hupy.config.json`, composing `init-copy-hooks`'s and `init-create-config`'s steps in one call. `_init_main(args)` flow, in order:
  1. `repo = load_git_repo(args.repo_path)` — see `load_git_repo` below
  2. resolve `repo_root = pathlib.Path(repo.working_tree_dir)` — deliberately *not* the raw `args.repo_path`, so that running `hupy init` from any subdirectory still anchors `hooks_dir`/`repo_root` at the true repository root
  3. resolve `hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)` — see Hook Integration Model for `_resolve_hooks_dir`'s `core.hooksPath`/`.git/hooks` fallback logic; `_resolve_hooks_dir` is imported from `cli_ich.py` (see that subcommand below), not defined locally
  4. `_copy_hook_stubs(hooks_dir, force)` (also from `cli_ich.py`) — `hooks_dir.mkdir(parents=True, exist_ok=True)` (no error if it already exists — see Hook Integration Model on why this is per-file, not directory-level), then for each file in `hupy/hook-stubs/`: if the target already exists, without `force` → `logger.error(...)` + `raise SystemExit(1)` (leaving that and any later files untouched); with `force`, `logger.warning(...)` then overwrites; otherwise reads the template text, substitutes `{{PYTHON}}` with `sys.executable` (see Hook Integration Model), writes it, and `shutil.copymode` (preserves the executable bit, since the substitution is a text read/write rather than `shutil.copy2`)
  5. `write_default_config(repo_root, force)` (`hupy/config/write_config.py`) — same existence/`force` pattern as step 4, but for a single file: `repo_root / CONFIG_FILENAME`, generated from `HupyConfigFile().model_dump_json(indent=2)` rather than copied from a static template
  - `_copy_hook_stubs`/`_resolve_hooks_dir` are imported **inside** `_init_main`, not at module level, because `cli_ich.py` imports `INIT_LOGGER_NAME`/`REPO_PATH_HELP`/`load_git_repo` back from `cli_init.py` at its own module level — a module-level import in the other direction would be a circular import
- **`init-create-config`** — implemented in `cli_icc.py`; standalone subcommand for step 5 above (`write_default_config(repo_root, force)`) only, for a repo that already has its hooks set up (or is managed some other way) and just needs the config file (re)written. Shares `load_git_repo`, `INIT_LOGGER_NAME`, and `REPO_PATH_HELP` from `cli_init.py`
- **`init-copy-hooks`** — implemented in `cli_ich.py`; standalone subcommand for steps 3–4 above (`_resolve_hooks_dir` + `_copy_hook_stubs`) only, for a repo that already has a config file and just needs the hook stubs (re)installed — e.g. after moving/recreating the virtualenv `hupy` is installed in (see Hook Integration Model's interpreter-path bullet). `_resolve_hooks_dir`/`_copy_hook_stubs` and their supporting constants (`_HOOK_STUBS_DIR`, `_PYTHON_PLACEHOLDER`) now live here rather than in `cli_init.py`
- **`load_git_repo(repo_path)`** — `git.Repo(repo_path, search_parent_directories=True)`; on `InvalidGitRepositoryError`/`NoSuchPathError`, `logger.exception(...)` then `raise SystemExit(1) from e`, **before** any filesystem writes happen. Used by `init`, `init-create-config`, `init-copy-hooks` (all via their respective `_*_main`), and `config.load_hupy_config` (via `hupy.cli.cli_init.load_git_repo`), so all resolve the same way from any subdirectory of the repo
- **`init`/`init-create-config`/`init-copy-hooks` CLI arguments**: all three share `REPO_PATH` (positional, optional, `type=pathlib.Path`, default=`pathlib.Path(os.getcwd())`, help text from the shared `REPO_PATH_HELP` constant) and `-v`/`-q` verbosity; `-f`/`--force` gates whichever of steps 4/5 above the subcommand performs; `--hooks-dir HOOKS_DIR` (`type=pathlib.Path`, default `None` → resolved in step 3) is only on `init` and `init-copy-hooks`, not `init-create-config`
- Known gap: `REPO_PATH`'s default is `pathlib.Path(os.getcwd())` evaluated once, when `register_cli_init_parser`/`register_cli_icc_parser`/`register_cli_ich_parser` run at module-import time — not per invocation. In a long-lived process (or across a test session that imports these modules once) this default is frozen to whatever the cwd was at first import, not the cwd at call time, despite the help text's "default=current working directory" implying otherwise. `tests/cli/` works around this by always passing `REPO_PATH` explicitly rather than relying on the default
- Known gap: `tests/cli/cli-cli_init_copy_hook_stubs_test.py`, `cli-cli_init_resolve_hooks_dir_test.py`, and `cli-cli_init_init_cli_test.py` still `from hupy.cli.cli_init import _copy_hook_stubs` / `_resolve_hooks_dir` / `_HOOK_STUBS_DIR`, which no longer exist there after the `init-copy-hooks` split moved them to `cli_ich.py` — these three test files fail to collect (`ImportError`) until updated to import from `cli_ich` instead
- Packaged templates: `hupy/hook-stubs/{pre-commit,prepare-commit-msg}` (thin `"{{PYTHON}}" -m hupy <stage>` wrappers, no `.bash` extension since git requires the exact hook name in the hooks directory), bundled via `[tool.setuptools.package-data]` in `pyproject.toml` (`hupy = ["hook-stubs/*"]`); `.hupy.config.json` is no longer a packaged file, since `write_default_config` generates its content from `HupyConfigFile` defaults instead of copying a template
- **`pre-commit`** (`cli_pre_commit.py`) — builds `repo = git.Repo(os.getcwd(), search_parent_directories=True)`, loads `.hupy.config.json` via `load_hupy_config(repo)`, applies `-v`/`-q` verbosity on top of `config.default_logger_verbosity`, then calls `perform_triage_tags_gating(repo)`; logs entry/exit via the logger (no nested subcommands)
- **`prepare-commit-msg`** (`cli_prepare_commit_msg.py`) — same `git.Repo`-build-then-config-load-then-verbosity pattern, then calls `prepend_commit_header(repo)`; logs entry/exit via the logger (no nested subcommands)
- **dispatch functions are module-level**, each in their own module (`cli_pre_commit._pre_commit_main`, `cli_prepare_commit_msg._prepare_commit_msg_main`) — they call the public functions from `ttg.tt_gating` and `pch.prepend_commit_header` directly, not via a CLI re-entry
- **verbosity** — both stage dispatch functions call `kamilog.set_logging_level_by_namespace(args, verbosity=config.default_logger_verbosity)`, so `.hupy.config.json`'s `default_logger_verbosity` sets the baseline and each `-v`/`-q` shifts it by one step; this targets the shared `PROJ_LOGGER_NAME` (`"HU"`) root logger, and child loggers (`"HU.TTG"`, `"HU.PCH"`, `"HU.CBM"`, `"HU.config-file"`, `"HU.VerGrep"`) inherit the resulting level since they set none of their own. `cli_init.py`'s `init` calls the same function but without a config (`set_logging_level_by_namespace(args, logger=logger)`, base `verbosity=0`), since `init` runs before any `.hupy.config.json` exists

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
- loggers created via `getLogger()` in `cbm` (`CBM_LOGGER_NAME`), `pch.prepend_commit_header`, `cli.cli_init`, `config.hupy_config_file` (`CONFIG_LOGGER_NAME`), `ver_grep`, and `ttg.tt_gating` each set `logger.propagate = False` — every logger already carries its own stdout/stderr handlers from `getLogger()`, so leaving propagation on would double-print every record through the root logger's handlers too
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
    cli_icc.py                    # `init-create-config` subcommand (config only)
    cli_ich.py                    # `init-copy-hooks` subcommand (hook stubs only)
    cli_pre_commit.py             # `pre-commit` dispatch
    cli_prepare_commit_msg.py      # `prepare-commit-msg` dispatch
  cbm/                             # Commit/Branch/Merge package (formerly flat commit_type.py)
    __init__.py                   # CBM_LOGGER_NAME = "HU.CBM"; re-exports below
    branch_type.py                 # BranchType enum + from_name(branch_name, repo)
    commit_type.py                 # CommitType flag + decide_commit_type(source, target)
    get_current_commit_type.py     # get_current_commit_type/get_source_branch/get_target_branch(repo)
  config/                         # HUPy config schema, load, and write helpers
    __init__.py                   # CONFIG_FILENAME = ".hupy.config.json"; CONFIG_LOGGER_NAME
    hupy_config_file.py            # HupyConfigFile pydantic model (schema + defaults); _VerGrep; _Cbm
    load_config.py                # load_hupy_config(repo): git.Repo in, read + validate, cache
    write_config.py               # write_default_config(repo_root, force)
  hook-stubs/                     # default hook stub scripts (packaged data)
    pre-commit                    # thin wrapper: `"{{PYTHON}}" -m hupy pre-commit`
    prepare-commit-msg            # thin wrapper: `"{{PYTHON}}" -m hupy prepare-commit-msg`
  kamilog.py                      # vendored logging module (v2.3.1)
  pch/                            # Prepend Commit Header package
    __init__.py                   # PCH_LOGGER_NAME = "HU.PCH"
    prepend_commit_header.py      # main function: rewrite COMMIT_EDITMSG; _HEADER_GENERATORS per merge type
  ttg/                            # Triage Tag Gating package
    __init__.py                   # TTG_LOGGER_NAME = "HU.TTG"
    tt_detect.py                  # scan staged diffs for TT markers
    tt_gating.py                  # gate commits by TT tier
  ver_grep/                       # version-grepping package (formerly flat ver_grep.py)
    __init__.py                   # VER_GREP_LOGGER_NAME = "HU.VerGrep"; re-exports below
    branch_version.py              # grep_source_branch_version()/grep_target_branch_version()
    version_bump.py                # decide_version_update_type(source_version, target_version)
docs/
  ttg_doc.md                      # user doc: TTG tiers & per-merge gating
  cbm_doc.md                      # user doc: CBM concepts + PCH merge-commit headers + ver_grep API
  hupy_config_doc.md               # user doc: .hupy.config.json fields & ver_grep setup
examples/
  hooks/                           # bash demos driving the real `hupy <stage>` CLI end-to-end
    pre-commit-demo.sh             # Feature Landing merge, steady+quiet TT only; expects PASS
    prepare-commit-msg-demo.sh     # Stable Release merge; expects header prepended
    all-hooks-demo.sh              # runs every demo in this folder in sequence (currently empty)
                                    # all three prep their repo by shelling out to tests/fixtures/prep_repo.py
  pch/                            # __init__.py (shared demo helpers) + 10 runnable demo scripts:
                                    # feature-landing, stable-release, sync-backport, catch-up,
                                    # hotfix-release, hotfix-backport, release-cut, release-backport,
                                    # skip-regular-commit, skip-unrelated-merge
  ttg/                            # __init__.py (shared demo helpers) + 6 runnable demo scripts:
                                    # {pass,fail}-{feature-landing,stable-release},
                                    # skip-{irrelevant-merge,non-merge-commit}
tests/
  conftest.py                     # root-level shared `repo_dir` fixture (tmp_path / "repo")
  cbm/                             # CBM-specific tests
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
  pch/                            # PCH-specific tests
    conftest.py                   # sys.path shim onto tests/fixtures/ for prep_repo import
    pch_helpers.py                # COMMIT_EDITMSG seed/read helpers
    pch-prepend_commit_header_skip_test.py
    pch-prepend_commit_header_feature_landing_test.py
    pch-prepend_commit_header_stable_release_test.py
    pch-prepend_commit_header_error_test.py
  ttg/                            # TTG-specific tests
    conftest.py                   # sys.path shim onto tests/fixtures/ for prep_repo import
    fixtures/                     # per-scenario fixture files used by prep_repo.py (tt_*.py, ...)
    ttg-tt_detect_test.py
    ttg-tt_gating_feature_landing_test.py
    ttg-tt_gating_stable_release_test.py
    ttg-tt_gating_non_merge_test.py
    ttg-tt_gating_regular_merge_test.py
    ttg-tt_gating_error_test.py
  fixtures/                       # fixtures shared by every suite (not package-specific)
    default_repo.bundle           # minimal git bundle fixture for repo cloning
    prep_repo.py                  # scenario repo generator (CLI + importable)
.hupy.config.json                 # this repo dogfoods hupy on itself; includes cbm section
pyproject.toml
```

### Testing Infrastructure

- **pytest fixtures** (`repo_dir`) — path under `tmp_path` for the scenario repo, populated by `prep_repo.py`; defined once in the root `tests/conftest.py` and shared by every suite (`tests/cli/conftest.py`'s `git_repo_dir` builds on it); fixtures are scoped per-test and auto-cleaned by `tmp_path`
- **git bundle fixture** (`tests/fixtures/default_repo.bundle`) — minimal single-file repo fixture; `prep_repo.py` clones it and dynamically constructs scenarios (branches, commits, MERGE_HEAD state, staged files from `tests/ttg/fixtures/*.py`)
- **`tests/fixtures/prep_repo.py`** — the shared repo-scenario builder, used by `tests/pch/`, `tests/ttg/` unit tests and, indirectly, by the `examples/pch/*-demo.py` and `examples/ttg/*-demo.py` demos. Exposes three builders: `prepare_repo(dest_dir, scenario)` for the legacy TTG/PCH `SCENARIOS` that unit tests also exercise (`non_merge_commit`, `irrelevant_merge`, `feature_landing_{pass,fail}`, `stable_release_{pass,fail}`), `prepare_repo_with_files(dest_dir, commit_bucket, files)` for an arbitrary file manifest against one of the `COMMIT_BUCKETS` (used by both unit tests and the `examples/ttg/*-demo.py` scripts), and `prepare_demo_repo(dest_dir, demo_bucket)` for the demo-only `DEMO_BUCKETS` (`sync_backport`, `catch_up`, `hotfix_release`, `hotfix_backport`, `release_cut`, `release_backport`) — no unit-test caller, since these 6 have no dedicated `tests/pch/` assertions yet, only `examples/pch/*-demo.py` scripts. **Known gap**: `DEMO_BUCKETS`'s in-code comment still claims these are "CBM merge types PCH does not yet handle" — stale, since `pch.prepend_commit_header`'s `_HEADER_GENERATORS` now covers all 6 (see `pch` in Module Details). Also runnable standalone as a CLI with mutually exclusive `--scenario <name>` / `--demo-bucket <name>` flags plus `--dest`, printing the prepared repo path; `examples/hooks/prepare-commit-msg-demo.sh` shells out to this CLI rather than re-implementing repo setup in bash.
- **`examples/pch/__init__.py`** / **`examples/ttg/__init__.py`** — aux helpers shared across each directory's `*-demo.py` scripts, deduplicated out of what was previously identical `_prepare_demo_repo`/`_run_*` code copy-pasted into every demo file. Each does the `sys.path.insert` onto `tests/fixtures/` and wraps `prep_repo.py`'s builders (`prepare_demo_repo_by_scenario`/`prepare_demo_repo_by_bucket` + `run_pch` for `pch`; `prepare_demo_repo` + `run_ttg` for `ttg`, the latter calling `perform_triage_tags_gating` directly rather than the full `pre-commit` CLI). Demo scripts pull these in with `from __init__ import ...` — this resolves because Python auto-adds a directly-run script's own directory to `sys.path`, so no additional path wiring is needed in the demo files themselves.
- **test file naming** — nested-package modules follow `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py` (e.g. `hupy/ttg/tt_gating.py` → `tests/ttg/ttg-tt_gating_*_test.py`, `hupy/cbm/branch_type.py` → `tests/cbm/cbm-branch_type_test.py`, `hupy/ver_grep/branch_version.py` → `tests/vg/vg-grep_*_branch_version_test.py`), split further by scenario group; `hupy/cbm/get_current_commit_type.py`'s three public functions each get their own file, nested under `tests/cbm/grct/` (the abbreviation mirrors the module name)
- **`tests/cli/`** (formerly `tests/setup/`, renamed with the `hupy/setup/` → `hupy/cli/` move) — unit tests for `_copy_hook_stubs` and `_resolve_hooks_dir` each get their own file (`cli-cli_init_copy_hook_stubs_test.py`, `cli-cli_init_resolve_hooks_dir_test.py`); the copy-stubs file also covers the `{{PYTHON}}` → `sys.executable` substitution (placeholder replaced, baked path absolute, packaged templates still carry the placeholder — see `cli` in Module Details). `write_default_config` (in `hupy/config/write_config.py`) has no dedicated test file of its own (see `config` in Module Details) and is instead exercised via `cli-cli_init_init_cli_test.py`, which asserts the written file matches `HupyConfig().model_dump_json(indent=2) + "\n"`. `cli-cli_init_init_cli_test.py` covers the CLI wiring end-to-end, since that's the other meaningful public surface (unlike `ttg`/`pch`, which test their public function directly without a separate CLI-wiring suite) — `cli_helpers.run_init_cli(args_list)` (formerly `setup_helpers.py`) builds a standalone `init` subparser via `register_cli_init_parser` and dispatches through it, exercising `--hooks-dir`/`-f`/`-v`/`-q` the same way the real `hupy` CLI would; `git_repo_dir` (in `conftest.py`) gives a fresh `git.Repo.init`-ed repo rather than reusing `ttg`'s scenario-bucket fixtures, since `init` doesn't care about commit type or branch state. Tests always pass `REPO_PATH` explicitly rather than relying on its default, since that default is frozen at module-import time (see `cli` in Module Details). 25 tests total — **currently broken**: all three files still import `_copy_hook_stubs`/`_resolve_hooks_dir`/`_HOOK_STUBS_DIR` from `hupy.cli.cli_init`, which moved to `hupy.cli.cli_ich` in the `init-copy-hooks` split (see the Known gap note under `cli` in Module Details); no dedicated test file exists yet for `cli_icc.py`/`cli_ich.py`'s own subcommand wiring.
- **`tests/cbm/`** — `cbm-branch_type_test.py` patches `hupy.cbm.branch_type.load_hupy_config` to stub `_Cbm` config (default and overridden branch names/prefixes, precedence between DEV/MAIN/HOTFIX/RELEASE/USER/FEATURE), confirming `repo` is forwarded through to `load_hupy_config`; `cbm-commit_type_test.py` parametrizes `CommitType.decide_commit_type` over all 8 known `(BranchType, BranchType)` pairs plus a set of unmapped pairs (all → `OTHER_MERGE`); `grct/` covers `get_current_commit_type`/`get_source_branch`/`get_target_branch` against real repo fixtures — regular commits, octopus/pull merges, detached HEAD, and per-repo caching behavior — with `grct/conftest.py` noting that repo construction/error handling is the caller's job, not these functions'.
- **`tests/vg/`** — `vg-decide_version_update_type_test.py` covers major/minor/patch bump classification, no-update and unparsable cases, and pre-release/build-suffix stripping; `vg-grep_source_branch_version_test.py`/`vg-grep_target_branch_version_test.py` (mirror images of each other) patch `hupy.ver_grep.branch_version.load_hupy_config` and use shared `vg_helpers.py` fixtures (`prepare_merge_repo_with_version`, `prepare_merge_repo_without_version_file`) to assert each function reads its own branch's tip specifically (not the other branch's, not the working tree), first-match-wins, not-configured returning `""`, and `SystemExit` on a missing version file or no matching line.
- **`tests/pch/pch-prepend_commit_header_stable_release_test.py`** — patches `hupy.pch.prepend_commit_header.grep_source_branch_version` (rather than `load_hupy_config`, since the version-string plumbing is already covered by `tests/vg/`) to assert the two header shapes: plain `"Stable Release"` when it returns `""`, `"Stable Release: <version>"` otherwise (semver and non-semver strings). 18 tests total in this file's package. The 6 newer merge types (`SYNC_BACKPORT`, `CATCH_UP`, `HOTFIX_RELEASE`, `HOTFIX_BACKPORT`, `RELEASE_CUT`, `RELEASE_BACKPORT`) have no equivalent dedicated test file yet — only `examples/pch/*-demo.py` scripts exercise them, one per type.
