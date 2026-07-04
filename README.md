# Hooks Utility Python `hupy` README

> **Hooks Utility Python** — a toolkit for enforcing commit quality via git hooks.

<!-- Fixme write readme w/ installation & usage -->


<!-- Todo add PCH more scenario eg keep up feature branch with dev -->
<!-- todo ban direct commit to main -->

> [!NOTE]
> Python reimplementation of the original bash `hooks_utility.sh`. Currently in **prototype**.













## ✨ Features

- 🛡️ **Branch protection** — block *annotation markers* (`TODO`, `FIXME`, `HACK`, `BUG`) by severity tier on protected branches
- 📋 **Ensure file edited** — require specific files or line ranges to change as part of a commit
- ✏️ **Improve commit message** — auto-generate better messages for merge commit types
- 🔍 **Commit type detection** — identify commit type (e.g., binary merge) from within a hook
