# hupy CONTEXT

*Last updated: 2026-07-27. This file describes the current architecture, not its evolution — for the full change history see `CHANGELOG.md`.*

## Project Overview

**hupy** (Hooks Utility Python) is a Python reimplementation of the bash `hooks_utility.sh` — a toolkit of utilities called from git hook scripts to enforce commit quality and branch hygiene.

Package `HUPy` (import name `hupy`) · build `setuptools` · Python `>=3.10` · install `pip install -e ".[dev]"` · dependencies `GitPython>=3.1`, `pydantic>=2`, `json5>=0.9`.

Implemented: `cbm`, `bdc`, `ttg`, `pt` (Paper Trail), `pch`, `ver_grep`, `config_file`, `state`, `should_run_module`, `stub`, `cli` (incl. `init`, `uninstall`), `kamilog`.

## Architecture

Each utility is a standalone module in `hupy/`, callable from any git hook script. Cross-module edges: within `ttg`; `pch`/`ttg`/`bdc`/`pt` → `cbm`; `cbm`/`ver_grep`/`bdc` → `config_file`; `bdc`/`ttg`/`pch`/`pt` → `should_run_module`, which itself depends on `config_file` and `state`.

| Module | Responsibility |
|---|---|
| `cli` | CLI entrypoint (`init`, `uninstall`, `verify`, `hook <stage>` × 17, `get`/`set`/`unset`/`info` accessors) |
| `cbm` | classify a branch name as a `BranchType` and an in-progress commit as a `CommitType` |
| `config_file` | pydantic schema + loading for `.hupy.config.jsonc` |
| `state` | pydantic schema + atomic I/O for `hupy-state.json` (verbosity, one-time skips) |
| `should_run_module` | combines a module's config `is_disabled` flag with its `skip_once` state flag into one run/skip decision |
| `stub` | render, write, and sync git hook stub scripts in a repo's hooks directory |
| `kamilog` | vendored logging with extra levels, ANSI color, diff compression, comment banners |
| `pch` | prepend header lines to in-progress merge commit messages, stamping the version via `ver_grep` |
| `ver_grep` | extract/compare a branch's version string across configured file occurrences (Version Uniformity) |
| `ttg` | Triage Tag Gating — scan staged diffs for triage tags, abort commits that introduce them on protected branches |
| `pt` | Paper Trail — assert at least one file matching a configured glob changed, aborting the commit otherwise |
| `bdc` | Ban Direct Commit — block a commit made directly on a protected branch, while still allowing merges into it |
| `hb` | Hook Bracket — run configured shell commands (`lead`/`trail`) around a hook stage |

### Design Principles

- **composable** — each utility works alone or combined inside a hook script
- **mostly stateless** — relies on git state and file diffs; the one exception is `hupy-state.json` (transient operator intent), kept out of the tracked `.hupy.config.jsonc`
- **simple defaults** — sensible behavior out of the box

### Hook Integration Model

`hupy init` sets a repo up with two artifacts:

1. **`.hupy.config.jsonc`** — tracked, dot-prefixed JSON5/JSONC config at the repo root, copied verbatim from `hupy/assets/.hupy.config.jsonc` (which documents every field via `//` comments).
2. **Hook stubs** — thin scripts, one per demanded git hook stage, rendered in-process and written into the repo's hooks directory (`core.hooksPath` if set, else `.git/hooks`). Each stub invokes `"<python>" -m hupy hook <stage> "$@"`.

Key decisions:

- **Config surface is the file, not the script** — enabling/ordering a feature is a config edit, not a bash edit.
- **`init`/`uninstall` are convergent, not conflict-aborting.** A demanded-but-missing file is always written; a file already present but differing is left alone and only reported unless `-f`/`--force`; a stub no longer demanded is left alone unless `--prune`. Both subcommands take a shared `--only {stubs,config}` flag (dict-dispatch registry) to scope to one artifact; plain `init`/`uninstall` acts on both. `-n`/`--dry-run` reports without writing.
- **Hook names come from demand, not a bundled asset directory** — every stage module under `hupy.cli.hooks` is auto-discovered, and a stage is demanded when its `hb` bracket is active or it defines `run_features`/`run_after`.
- **`verify` is strictly read-only** — never opens `hupy-state.json`, reports (never enforces) Version Uniformity and hook stub drift; exits nonzero only on a missing/malformed config file. Repair always goes through `hupy init`.
- **Interpreter path baked in at install time** — each stub is rendered with `sys.executable`; re-run `hupy init -f` after moving the venv.
- **Enforcement caveat**: git hooks are client-side and opt-in (`--no-verify` bypasses them); guaranteed enforcement needs a server-side mechanism, out of scope here.

## Module Notes

- **`cbm`** — `BranchType` (`FEATURE`/`DEV`/`MAIN`/`HOTFIX`/`RELEASE`/`USER`) classified from config-driven name patterns; `CommitType` (a `Flag`) maps `(source, target)` `BranchType` pairs to eight merge types via `decide_commit_type`. See `docs/cbm_doc.md` for the full tables.
- **`pch`** — rewrites `.git/COMMIT_EDITMSG` per `CommitType` with a header naming the merge kind, version, and bump size (`Major`/`Minor`/`Patch`); `VERSION_RELEASE` additionally picks Alpha/Beta/RC/Pre-Alpha/Vertical-Slice/Prototype/Stable wording from the version core plus configured tags.
- **`config_file`** — `HupyConfigFile` pydantic schema, nested per-module sections (`vg`/`cbm`/`bdc`/`ttg`/`pt`/`pch`/`hb`), each with an `is_disabled` flag; the shipped asset is the sole source of field defaults (schema itself carries almost none).
- **`state`** — `HupyStateFile` (`hooks_logger_verbosity`, `skip_once`, `chain_session`) resolved inside `.git/`, loaded/saved via `open_state_file(repo)` (thread- and process-safe, atomic).
- **`should_run_module`** — single run/skip gate combining config `is_disabled` and state `skip_once`, used by `bdc`/`ttg`/`pt`/`pch`/`hb`/`vg`.
- **`stub`** — `sync_hook_stubs`/`check_hook_stubs`/`uninstall_hook_stubs` classify each demanded name's file as missing/stale/unused and act (or just report) accordingly; `get_hook_names_by_demand` is the sole source of truth for which stages need a stub.
- **`ver_grep`** — greps a version string from a configured file occurrence, at a git ref or the on-disk `WORKTREE`; `check_version_uniformity` compares every other configured occurrence against the canonical one and can hard-fail a commit.
- **`ttg`** — detects triage tags in staged diff additions (tier- and comment-aware), gates by commit type (`FEATURE_LANDING` → Loud tags, `VERSION_RELEASE` → Loud+Steady), reports and aborts on a match.
- **`pt`** — requires at least one staged file to match a configured glob per merge/commit type; runs in `pre-commit`/`pre-merge-commit`/`pre-applypatch`, deliberately not `pre-rebase` (a rebase replays existing commits rather than introducing new content).
- **`bdc`** — blocks a commit landing directly on a protected branch (`main`/`dev`/configured names) while allowing merges; wired into `pre-commit`, `pre-rebase`, `pre-applypatch`.
- **`hb`** — runs configured `lead`/`trail` shell commands around a hook stage, filtered by commit type, via `subprocess.run(..., shell=True, executable="/bin/bash")`.
- **`cli`** — `cli_main.py` dispatches eight top-level subcommands (`init`, `uninstall`, `hook <stage>` × 17, `verify`, `get`/`set`/`unset`/`info` accessors). `cli_hook.py`'s generic `_run_hook_stage` runner opens state, applies verbosity, adopts the chain session by parent PID, runs the `hb` lead bracket → stage's `run_features` → `hb` trail bracket → `run_after`, then closes the chain (`state_file.reset_for_next_chain()`) on whichever stage `chain_policy.is_chain_terminal` names for that chain type. Accessors (`hupy-version`, `verbosity`, `skip-once`, `branch-type`, `grep-ver`, `current-commit-type`) share one generic get/set/unset/info runner in `cli_accessors.py`.
  - **Known gap**: `chain_policy.detect_amend(hook_args)` over-predicts an amend for git's `-c <commit>`/`-C <commit>` (not just `--amend`), so `post-commit` occasionally yields its chain-close to a `post-rewrite` that never fires — cosmetic (self-corrects next chain), marked `# fixme` in-code (Quiet tier).
- **`kamilog`** — vendored logging (v2.3.1) adding `.enter()`/`.skip()`/`.succ()`/`.pass_()`/`.done()`/`.fail()` levels, ANSI color, and comment-banner helpers; shared `"HU"` root logger, per-module children with `propagate = False`.

## Annotation Markers

Gating operates on *triage tags* in three tiers — **Loud** (all-caps `TODO`/`FIXME`/`HACK`/`BUG`, blocked by default), **Steady** (title-case, configurable), **Quiet** (lowercase, configurable). Full taxonomy is in the global `CLAUDE.md` under **Triage Tags**.

## Package Layout

```
hupy/                    # installable package
  cli/                   # parsing & dispatch: init, uninstall, verify, hook/<stage>, accessors/
  cbm/                   # branch/commit classification
  bdc/                   # Ban Direct Commit
  config_file/           # .hupy.config.jsonc schema, load, write
  state/                 # hupy-state.json schema and I/O
  should_run_module.py   # shared run/skip gate
  stub/                  # git hook stub generation & sync
  assets/.hupy.config.jsonc  # default config, commented; copied verbatim
  kamilog.py             # vendored logging
  pch/                   # prepend commit header
  ttg/                   # Triage Tag Gating
  pt/                    # Paper Trail
  ver_grep/              # version grepping & Version Uniformity
docs/                    # ttg_doc, pt_doc, cbm_doc, chain_doc, stub_doc
examples/                # bash/py demo scripts per module + full-chain demos
tests/                   # pytest suite, mirrors hupy/ layout; fixtures/ holds shared repo scenarios
.hupy.config.jsonc       # this repo dogfoods hupy on itself
pyproject.toml
```

### Testing Infrastructure

- **Fixtures** — `tests/conftest.py` provides `repo_dir`; `tests/fixtures/prep_repo.py` builds scenario repos from a git bundle; `tests/fixtures/config_fixture.py` deep-merges overrides onto the shipped default config.
- **Test file naming** — mirrors source: `hupy/<pkg>/<mod>.py` → `tests/<pkg>/<pkg>-<mod>_test.py`.
- **Coverage notes** — the six newer merge types have only `examples/pch/*-demo.py` scripts, no dedicated `tests/pch/` assertions yet.
