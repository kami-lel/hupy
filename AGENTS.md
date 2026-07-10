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

Test file naming: test layout mirrors source layout — top-level modules map directly (`hupy/commit_type.py` → `tests/commit_type_test.py`); packages nest (`hupy/ttg/tt_gating.py` → `tests/ttg/ttg-tt_gating_*_test.py`, split further by scenario group). Fixtures shared by every suite (the git bundle, the repo-scenario builder) live in `tests/fixtures/`, not colocated with any one package's tests; `tests/pch/` and `tests/ttg/` each `sys.path.insert` that directory in their `conftest.py` to import `prep_repo`.

The shared `repo_dir` pytest fixture (`tmp_path / "repo"`) lives in the root `tests/conftest.py` and applies to every suite. Repo scenarios are built by `tests/fixtures/prep_repo.py`, which clones the shared git bundle (`tests/fixtures/default_repo.bundle`) and dynamically constructs branches/commits/merge state — reused across unit tests and the `examples/pch/` and `examples/ttg/` demo scripts, and runnable standalone as a CLI:

```bash
python3 tests/fixtures/prep_repo.py --scenario stable_release_pass --dest /tmp/demo_repo
python3 tests/fixtures/prep_repo.py --demo-bucket hotfix_backport --dest /tmp/demo_repo
```

`--scenario` covers TTG/PCH scenarios that unit tests also exercise; `--demo-bucket` covers CBM merge types PCH doesn't handle yet, used only by the `examples/pch/*-demo.py` skip demos. Bash demos in `examples/hooks/` (e.g. `pre-commit-demo.sh`, `prepare-commit-msg-demo.sh`) shell out to this same CLI rather than re-implementing repo setup in bash.

`examples/pch/__init__.py` and `examples/ttg/__init__.py` hold the aux helpers shared across their sibling `*-demo.py` scripts (repo prep + running the library call), imported back with `from __init__ import ...` — each demo script's own directory lands on `sys.path` automatically since it's run standalone (`python3 examples/pch/<name>-demo.py`), so this resolves without extra `sys.path` wiring.

## PR & Commit Instructions

- follow the **Git Command Safety Policy** in `CLAUDE.md` — never run reset, push, rebase, etc.
- keep commits atomic and scoped to a single utility or change
- update `CHANGELOG.md` under `[Unreleased]` for every user-visible change

## Documentation Maintenance

- update `AGENTS.md` when commands, conventions, or constraints change
- update `CONTEXT.md` when architecture, module boundaries, or design decisions change
- never duplicate content between the two files
