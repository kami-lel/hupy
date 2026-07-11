# `hupy` (Hooks Utility Python) README

> a toolkit for enforcing commit quality via git hooks.

> [!NOTE]
> Python reimplementation of the original bash [hooks-utility](https://github.com/kami-lel/hooks-utility).

<!-- todo reimplement ensure file modified -->













## ✨ Features

- 🚫 [**Ban Direct Commit**](docs/bdc_doc.md) — block commits made directly on a protected branch (`main` by default), while still allowing that branch to receive commits through a merge
- 🛡️ [**Triage Tag Gating**](docs/ttg_doc.md) — block *annotation markers* (`TODO`, `FIXME`, `HACK`, `BUG`) by severity tier on protected branches
- ✏️ [**Prepend Commit Header**](docs/pch_doc.md) — auto-generate descriptive headers for merge commit types, stamping the project version on releases
- 🔗 [**Hook Bracket**](docs/hb_doc.md) — run your own lead/trail shell commands around each hook stage, no custom hook required













## 📦 Installation

#### Install Python Package

**Clone and install locally**

```bash
git clone https://github.com/kami-lel/hupy.git
cd hupy
pip install .
```

Or install **directly from GitHub**

```bash
pip install git+https://github.com/kami-lel/hupy.git
```



#### Set Up for Repository

Initialize `hupy` inside the git repository to protect:

```bash
hupy init
```

- copies the default hook stub scripts into the repo's hooks directory
- writes a default `.hupy.config.jsonc` at the repository root — commit it, so every clone shares the same behavior; each section is commented in place with what it controls

Verify the config file at any time:

```bash
hupy verify-config-file
```













## 🚀 Usage

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — there is nothing extra to run. From then on every `git commit` fires them, and git hands each one to the matching *HUPy* feature.

See [Hook Flow Documentation](docs/flow_doc.md) for the end-to-end diagram of how each stage runs.

See the per-feature docs for detailed usage:

- [Commit, Branch & Merge (CBM)](docs/cbm_doc.md) — shared branch and merge type classification
- [Ban Direct Commit (BDC)](docs/bdc_doc.md)
- [Triage Tag Gating (TTG)](docs/ttg_doc.md)
- [Prepend Commit Header (PCH)](docs/pch_doc.md)
- [Hook Bracket (HB)](docs/hb_doc.md)

#### Other Commands

- `hupy skip-once` — skip a module (`vg`, `ttg`, `pch`, `bdc`, `hb`) for exactly one upcoming hook run
- `hupy set-verbosity` — set the base logging verbosity used during hook runs
