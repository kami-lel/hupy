# `hupy` (Hooks Utility Python) README

> a toolkit for enforcing commit quality via git hooks.

> [!NOTE]
> Python reimplementation of the original bash [hooks-utility](https://github.com/kami-lel/hooks-utility).

<!--
Todo reimplement ensure file modified
Fixme linguo: flow -> chain
Fixme linguo: hook vs a core logic etc?
Fixme linguo: HB what are HB "commands"
-->













## ✨ Features

- 🚫 [**Ban Direct Commit**](docs/bdc_doc.md) — block commits made directly on a protected branch (`main` by default), while still allowing that branch to receive commits through a merge
- 🛡️ [**Triage Tag Gating**](docs/ttg_doc.md) — block *annotation markers* (`TODO`, `FIXME`, `HACK`, `BUG`) by severity tier on protected branches
- ✏️ [**Prepend Commit Header**](docs/pch_doc.md) — auto-generate descriptive headers for merge commit types, stamping the project version on releases
- 🔗 [**Hook Bracket**](docs/hb_doc.md) — run your own lead/trail shell commands around each hook stage, no custom hook required













## 📦 Installation

<!--
Fixme move to install doc
Todo doc for using pyproject.toml & setup.cfg
-->

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

Verify the HUPy setup at any time:

```bash
hupy verify
```

`verify` checks that:

- the config file (`.hupy.config.jsonc`) loads and validates against the schema
- the version string can be grepped
- every packaged hook stub is installed in the repo's hooks directory













## 🚀 Usage

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — there is nothing extra to run. From then on every `git commit` fires them, and git hands each one to the matching *HUPy* feature.

See [Hook Flow Documentation](docs/flow_doc.md) for the end-to-end diagram of how each stage runs.

See the per-feature docs for detailed usage:

- [Commit, Branch & Merge (CBM)](docs/cbm_doc.md) — shared branch and merge type classification
- [Ban Direct Commit (BDC)](docs/bdc_doc.md)
- [Triage Tag Gating (TTG)](docs/ttg_doc.md)
- [Prepend Commit Header (PCH)](docs/pch_doc.md)
- [Hook Bracket (HB)](docs/hb_doc.md)






### `skip-once` command

Need to get a single commit through without loosening the config — a hotfix under time pressure, a false positive from TTG, a merge PCH mis-classifies? Rather than editing `.hupy.config.jsonc` and remembering to revert it, skip the offending module(s) (`vg`, `ttg`, `pch`, `bdc`, `hb`) for just the next hook run:

```bash
hupy skip-once MODULE [MODULE ...]
```

The skip is consumed automatically by the next `pre-commit`/`prepare-commit-msg` run, so behavior snaps back to normal right after. Change your mind first? Pass `-u`/`--unset` to clear a pending skip.






### `set-verbosity` command

Turn up logging when a hook's behavior looks wrong and you need to see what *HUPy* is actually deciding, or turn it down to keep commits quiet day-to-day:

```bash
hupy set-verbosity [VERBOSITY]
```

Unlike `skip-once`, this setting persists across hook runs until changed again; defaults to `1` when `VERBOSITY` is omitted.
