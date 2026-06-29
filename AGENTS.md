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

## Code Style

- follow variable naming, comment format, and banner conventions from the global `CLAUDE.md`
- function names start with a verb: `check_branch`, `detect_commit_type`
- boolean functions and variables start with `is_` or `has_`: `is_protected`, `has_marker`
- constants in `UPPER_CASE_WITH_UNDERSCORES`
- max 80 chars per line

## Testing Instructions

Scope runs to changed modules, not the full suite:

```bash
pytest tests/test_<module>.py
```

Full suite (pre-merge only):

```bash
pytest tests/
```

Test files mirror source: `hupy/foo.py` → `tests/test_foo.py`

## PR & Commit Instructions

- follow the **Git Command Safety Policy** in `CLAUDE.md` — never run reset, push, rebase, etc.
- keep commits atomic and scoped to a single utility or change
- update `CHANGELOG.md` under `[Unreleased]` for every user-visible change

## Documentation Maintenance

- update `AGENTS.md` when commands, conventions, or constraints change
- update `CONTEXT.md` when architecture, module boundaries, or design decisions change
- never duplicate content between the two files
