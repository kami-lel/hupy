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

Test layout mirrors source layout: `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py`, split further by scenario group (e.g. `hupy/ttg/gate_tt.py` → `tests/ttg/ttg-gate_tt_*_test.py`, `hupy/cbm/get_current_commit_type.py` → `tests/cbm/grct/cbm-grct-*_test.py`). A top-level module with no package (`hupy/should_run_module.py`) gets its own directory, dropping the `<pkg>-` prefix.

Cross-suite fixtures live in `tests/fixtures/`, not colocated with any package. The root `tests/conftest.py` defines the shared `repo_dir` fixture (`tmp_path / "repo"`). Suites that need `prep_repo` or `config_fixture` `sys.path.insert(tests/fixtures)` in their own `conftest.py`. Build config via `config_fixture.load_config_fixture(overrides)` — deep-merges onto the shipped asset — never by constructing `HupyConfigFile` from partial kwargs (its fields carry no defaults).

Repo scenarios are built by `tests/fixtures/prep_repo.py`, which clones the git bundle (`tests/fixtures/default_repo.bundle`), constructs branches/commits/merge state, and copies the shipped `DEFAULT_CONFIG_ASSET` onto each repo as an untracked `.hupy.config.jsonc`. Also runnable standalone:

```bash
python3 tests/fixtures/prep_repo.py --scenario version_release_pass --dest /tmp/demo_repo
python3 tests/fixtures/prep_repo.py --demo-bucket hotfix_backport --dest /tmp/demo_repo
```

`--scenario` covers TTG/PCH cases unit tests also exercise; `--demo-bucket` backs the `examples/pch/*-demo.py` scripts. The `examples/hooks/*.sh` bash demos shell out to this same CLI. `examples/{pch,ttg,bdc}/__init__.py` hold repo-prep + library-call helpers shared across their `*-demo.py` scripts, imported with `from __init__ import ...` (a run script's own directory is auto-added to `sys.path`).

## PR & Commit Instructions

- follow the **Git Command Safety Policy** in `CLAUDE.md` — never run reset, push, rebase, etc.
- keep commits atomic and scoped to a single utility or change
- update `CHANGELOG.md` under `[Unreleased]` for every user-visible change

## Documentation Maintenance

- update `AGENTS.md` when commands, conventions, or constraints change
- update `CONTEXT.md` when architecture, module boundaries, or design decisions change
- never duplicate content between the two files
