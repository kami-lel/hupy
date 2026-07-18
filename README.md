# `hupy` (Hooks Utility Python) README

> a toolkit for enforcing commit quality via git hooks.

> [!NOTE]
> Python reimplementation of the original bash [hooks-utility](https://github.com/kami-lel/hooks-utility).













## ✨ Features

- 🚫 **Ban Direct Commit** — tired of teammates pushing straight to `main`? block direct commits on protected branches while merges still sail through
- 🛡️ **Triage Tag Gating** — stop a stray `TODO`/`FIXME`/`HACK`/`BUG` from sneaking onto a protected branch, gated by severity tier
- 📝 **Paper Trail** — require a changelog entry, migration, or other companion file to actually change alongside the commit it belongs with
- ✏️ **Prepend Commit Header** — merge commits that write their own descriptive headers and stamp the version on every release, no manual typing
- 🔗 **Hook Bracket** — wrap any git hook stage with your own lead/trail shell commands, without hand-rolling a custom hook script













## 📦 Installation

See [Installation Documentation](docs/install_doc.md) for cloning, package install, and repository setup steps.













## 🚀 Usage

Clone the repo and install the package per [Installation](docs/install_doc.md), then run `hupy init` inside your repository to drop in the hook stubs. From there the hooks are **fully automatic** — every `git commit` fires them, and git hands each one to the matching *HUPy* feature:

- [Hook Chain](docs/chain_doc.md) — the diagram of how each stage runs and hands off to the next
- [Hook Stub](docs/stub_doc.md) — how `hupy init`/`hupy verify` decide which stubs to install, and how a repeat `hupy verify` keeps them, the config, and the version grep in sync afterward

Every feature reasons about commits the same way, via the shared [Commit, Branch & Merge (CBM)](docs/cbm_doc.md) classification of branches and merge types, then layers its own behavior on top:

- [Ban Direct Commit (BDC)](docs/bdc_doc.md) — keeps commits off protected branches unless they arrive through a merge
- [Triage Tag Gating (TTG)](docs/ttg_doc.md) — gates `TODO`/`FIXME`/`HACK`/`BUG` markers by severity tier
- [Paper Trail (PT)](docs/pt_doc.md) — requires configured files to have changed alongside the commit
- [Prepend Commit Header (PCH)](docs/pch_doc.md) — writes merge headers and stamps release versions
- [Hook Bracket (HB)](docs/hb_doc.md) — wraps any hook stage with your own lead/trail shell commands

Each doc above covers its own config in full. Beyond the hooks themselves, `hupy` keeps a small amount of its own config/state — a one-time module skip, the hook logger's verbosity — behind a shared `get`/`set`/`unset`/`info` command group. Run `hupy -h`, or `-h` on any subcommand, to see exactly what's there; the help text stays current, so it beats reading it here secondhand.
