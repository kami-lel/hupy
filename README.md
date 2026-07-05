# Hooks Utility Python `hupy` README

> **Hooks Utility Python** — a toolkit for enforcing commit quality via git hooks.

<!--
todo add PCH more scenario eg keep up feature branch with dev
todo ban direct commit to main
Todo set up self for HUPy
-->

> [!NOTE]
> Python reimplementation of the original bash `hooks_utility.sh`. Currently in **prototype**.













## ✨ Features

- 🛡️ **Branch protection** — block *annotation markers* (`TODO`, `FIXME`, `HACK`, `BUG`) by severity tier on protected branches
- 📋 **Ensure file edited** — require specific files or line ranges to change as part of a commit
- ✏️ **Improve commit message** — auto-generate better messages for merge commit types
- 🔍 **Commit type detection** — identify commit type (e.g., binary merge) from within a hook













## 📦 Installation

#### Install Python Package

**Clone and install locally**

```bash
git clone https://github.com/kami-lel/hooks-utility-py.git
cd hooks-utility-py
pip install .
```

Or install **directly from GitHub**

```bash
pip install git+https://github.com/kami-lel/hooks-utility-py.git
```



#### Set Up for Repository

Initialize `hupy` inside the git repository to protect:

```bash
python -m hupy init
```

- copies the default hook scripts into `scripts/hupy-hooks/`
- points git's `core.hooksPath` at that folder

<!-- Fixme this whole section describes the superseded scripts/hupy-hooks/
+ core.hooksPath design; update to the .hupy.config.json + .git/hooks/
stub design once `init` is reimplemented, per CONTEXT.md's Hook
Integration Model -->



#### Customize the hooks

Inspect the copied scripts and comment out any step not needed:

- `scripts/hupy-hooks/pre-commit`
- `scripts/hupy-hooks/prepare-commit-msg`

<!-- Fixme superseded — customization moves to editing the tracked
.hupy.config.json instead of commenting out lines in copied scripts -->













## 🚀 Usage

See the per-feature docs for detailed usage:

- [Triage Tag Gating (TTG)](docs/ttg_doc.md)
- [Prepend Commit Header (PCH)](docs/pch_doc.md)
