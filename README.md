# `hupy` (Hooks Utility Python) README

> a toolkit for enforcing commit quality via git hooks.

> [!NOTE]
> Python reimplementation of the original bash [hooks-utility](https://github.com/kami-lel/hooks-utility).













## ✨ Features

- 🚫 **Ban Direct Commit** — tired of teammates pushing straight to `main`? block direct commits on protected branches while merges still sail through
- 🛡️ **Triage Tag Gating** — stop a stray `TODO`/`FIXME`/`HACK`/`BUG` from sneaking onto a protected branch, gated by severity tier
- 📝 **Paper Trail** — require a changelog entry, migration, or other companion file to actually change alongside the commit it belongs with
- 🔢 **Version Uniformity** — catch a version bumped in one file but forgotten in another — a shipped config asset, a README badge — before a release merge lands
- ✏️ **Prepend Commit Header** — merge commits that write their own descriptive headers and stamp the version on every release, no manual typing
- 🔗 **Hook Bracket** — wrap any git hook stage with your own lead/trail shell commands, without hand-rolling a custom hook script













## 📦 Install

### Clone and Install Locally

```bash
git clone https://github.com/kami-lel/hupy.git
cd hupy
pip install .
```

### Install Directly from GitHub

```bash
pip install git+https://github.com/kami-lel/hupy.git
```

### Add as a Project Dependency

To pull `hupy` in automatically whenever your project's dependencies are installed, declare it in `pyproject.toml`:

```toml pyproject.toml
[project]
dependencies = [
    "hupy @ git+https://github.com/kami-lel/hupy.git",
]
```

Or, for projects still using `setup.cfg`:

```cfg setup.cfg
[options]
install_requires =
    hupy @ git+https://github.com/kami-lel/hupy.git
```













## ⚙️ Setup

Initialize `hupy` inside the git repository to protect:

```bash
hupy init
```

- renders the demanded hook stub scripts into the repo's hooks directory
- writes a default `.hupy.config.jsonc` at the repository root — commit it, so every clone shares the same behavior; each section is commented in place with what it controls

`hupy init` is convergent: it's safe to run again at any time. Files already correct are left untouched, missing ones are written, and nothing already present is rewritten or removed unless you pass `-f`/`--force` (rewrite) or `--prune` (remove no-longer-demanded stubs). Re-run it after upgrading `hupy`, editing `.hupy.config.jsonc`, or moving the virtual environment (`hupy init -f`, since the interpreter path is baked into each stub).

Verify the HUPy setup at any time, without changing anything:

```bash
hupy verify
```

`verify` checks that:

- the config file (`.hupy.config.jsonc`) loads and validates against the schema
- the version string can be grepped
- every demanded hook stub is installed in the repo's hooks directory and matches what HUPy currently renders

It's strictly read-only: it never writes or deletes a file. Run `hupy init` to fix whatever it reports.

To remove `hupy` from a repository, reversing `hupy init`:

```bash
hupy uninstall --force
```

> [!IMPORTANT]
> Without `--force` it's a dry run, reporting what would be removed.













## 🚀 Usage

Clone the repo and install the package per [Installation](#-installation), then run `hupy init` inside your repository to drop in the hook stubs. From there the hooks are **fully automatic** — every `git commit` fires them, and git hands each one to the matching *HUPy* feature:

- [Hook Chain](docs/chain_doc.md) — the diagram of how each stage runs and hands off to the next
- [Hook Stub](docs/stub_doc.md) — how `hupy init`/`hupy verify` decide which stubs to install, and how a repeat `hupy init` keeps them and the config file in sync afterward

Every feature reasons about commits the same way, via the shared [Commit, Branch & Merge (CBM)](docs/cbm_doc.md) classification of branches and merge types, then layers its own behavior on top:

- [Ban Direct Commit (BDC)](docs/bdc_doc.md) — keeps commits off protected branches unless they arrive through a merge
- [Triage Tag Gating (TTG)](docs/ttg_doc.md) — gates `TODO`/`FIXME`/`HACK`/`BUG` markers by severity tier
- [Paper Trail (PT)](docs/pt_doc.md) — requires configured files to have changed alongside the commit
- [Version Grep (VG)](docs/vg_doc.md) — greps the canonical version and checks every other configured occurrence for Version Uniformity
- [Prepend Commit Header (PCH)](docs/pch_doc.md) — writes merge headers and stamps release versions
- [Hook Bracket (HB)](docs/hb_doc.md) — wraps any hook stage with your own lead/trail shell commands

Each doc above covers its own config in full. Beyond the hooks themselves, `hupy` keeps a small amount of its own config/state — a one-time module skip, the hook logger's verbosity — behind a shared `get`/`set`/`unset`/`info` command group. Run `hupy -h`, or `-h` on any subcommand, to see exactly what's there; the help text stays current, so it beats reading it here secondhand.
