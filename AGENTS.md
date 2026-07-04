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

Test file naming: test layout mirrors source layout — top-level modules map directly (`hupy/commit_type.py` → `tests/commit_type_test.py`); packages nest (`hupy/ttg/tt_gating.py` → `tests/ttg/ttg-tt_gating_*_test.py`, split further by scenario group); when a package's tests need fixtures from another test directory (e.g., `tests/pch/` needs `tests/ttg/prep_repo.py`), import cross-directory rather than colocating test files by fixture convenience.

Tests use a `repo_dir` pytest fixture (`tests/conftest.py` or `tests/<pkg>/conftest.py`) plus a shared git bundle fixture (`tests/testee/default_repo.bundle`) that is cloned and dynamically modified per test for minimal storage and fast setup.

## PR & Commit Instructions

- follow the **Git Command Safety Policy** in `CLAUDE.md` — never run reset, push, rebase, etc.
- keep commits atomic and scoped to a single utility or change
- update `CHANGELOG.md` under `[Unreleased]` for every user-visible change

## Documentation Maintenance

- update `AGENTS.md` when commands, conventions, or constraints change
- update `CONTEXT.md` when architecture, module boundaries, or design decisions change
- never duplicate content between the two files
