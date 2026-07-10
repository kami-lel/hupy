---
name: hupy AGENTS
alwaysApply: true
---

# hupy AGENTS

## Setup Commands

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Testing Instructions

Scope runs to changed modules, not the full suite:

```bash
pytest tests/<module>_test.py
pytest tests/<pkg>/
```

Full suite (pre-merge only):

```bash
pytest tests/
```

Test file naming: test layout mirrors source layout — packages nest (`hupy/cbm/branch_type.py` → `tests/cbm/cbm-branch_type_test.py`, `hupy/cbm/get_current_commit_type.py` → `tests/cbm/grct/cbm-grct-*_test.py`; `hupy/ver_grep/branch_version.py` → `tests/vg/vg-grep_*_branch_version_test.py`; `hupy/ttg/gate_tt.py` → `tests/ttg/ttg-gate_tt_*_test.py`; `hupy/bdc/ban_direct_commit.py` → `tests/bdc/bdc-ban_direct_commit_test.py`; `hupy/config/config_file.py` → `tests/config/config-shipped_config_file_test.py`; `hupy/state/state_file.py` → `tests/state/state-consume_skip_once_test.py`), split further by scenario group. A top-level module with no enclosing package (`hupy/should_run_module.py`) still gets its own directory under `tests/`, dropping the `<pkg>-` filename prefix since there's no package to name (`tests/should_run_module/should_run_module_test.py`). Fixtures shared by every suite (the git bundle, the repo-scenario builder, the config fixture) live in `tests/fixtures/`, not colocated with any one package's tests; `tests/pch/` and `tests/ttg/` each `sys.path.insert` that directory in their `conftest.py` to import `prep_repo`; `tests/cbm/`, `tests/bdc/`, and `tests/should_run_module/` do the same to import `tests/fixtures/config_fixture.py`'s `load_config_fixture(overrides)` — build a validated `HupyConfigFile` by deep-merging `overrides` onto the shipped default config asset (`hupy/assets/.hupy.config.jsonc`, exposed as `DEFAULT_CONFIG_ASSET` in `hupy/config/config_file_path.py`), replacing the old pattern of constructing `HupyConfigFile` straight from partial kwargs (no longer possible now that its fields carry no defaults).

The shared `repo_dir` pytest fixture (`tmp_path / "repo"`) lives in the root `tests/conftest.py` and applies to every suite. Repo scenarios are built by `tests/fixtures/prep_repo.py`, which clones the shared git bundle (`tests/fixtures/default_repo.bundle`) and dynamically constructs branches/commits/merge state — reused across unit tests and the `examples/pch/` and `examples/ttg/` demo scripts, and runnable standalone as a CLI. The bundle no longer carries a committed `.hupy.config.jsonc`; `prep_repo.py` copies the shipped `DEFAULT_CONFIG_ASSET` straight onto disk as each scenario repo's `.hupy.config.jsonc`, untracked, for `load_hupy_config` to read.

```bash
python3 tests/fixtures/prep_repo.py --scenario version_release_pass --dest /tmp/demo_repo
python3 tests/fixtures/prep_repo.py --demo-bucket hotfix_backport --dest /tmp/demo_repo
```

`--scenario` covers TTG/PCH scenarios that unit tests also exercise; `--demo-bucket` covers CBM merge types PCH doesn't handle yet, used only by the `examples/pch/*-demo.py` skip demos. Bash demos in `examples/hooks/` (e.g. `pre-commit-demo.sh`, `prepare-commit-msg-demo.sh`) shell out to this same CLI rather than re-implementing repo setup in bash.

`examples/pch/__init__.py`, `examples/ttg/__init__.py`, and `examples/bdc/__init__.py` hold the aux helpers shared across their sibling `*-demo.py` scripts (repo prep + running the library call), imported back with `from __init__ import ...` — each demo script's own directory lands on `sys.path` automatically since it's run standalone (`python3 examples/pch/<name>-demo.py`), so this resolves without extra `sys.path` wiring.

## PR & Commit Instructions

- follow the **Git Command Safety Policy** in `CLAUDE.md` — never run reset, push, rebase, etc.
- keep commits atomic and scoped to a single utility or change
- update `CHANGELOG.md` under `[Unreleased]` for every user-visible change

## Documentation Maintenance

- update `AGENTS.md` when commands, conventions, or constraints change
- update `CONTEXT.md` when architecture, module boundaries, or design decisions change
- never duplicate content between the two files
