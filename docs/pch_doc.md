# Prepend Commit Header (PCH) Documentation

**Prepend Commit Header** is *HUPy*'s `prepare-commit-msg` hook. When you make a **merge commit**, it adds a short header line to the top of the commit message so the history reads clearly at a glance — you don't have to write it yourself.

It recognizes two merge types and leaves every other commit untouched.

## What It Does

| Merge | Header added |
|---|---|
| **Feature Landing** — a feature branch merged into `dev` | `Feature Landing: <branch-name>` |
| **Stable Release** — `dev` merged into `main` | `Stable Release: <version>` |
| anything else (regular commit, unrelated merge) | *nothing — message untouched* |

The header goes on the first line, followed by a blank line and then git's original message:

```
Feature Landing: add-user-auth

Merge branch 'add-user-auth' into dev
```

## Version Number

On a **Stable Release**, the header includes your project's version — e.g. `Stable Release: 1.0.0`. That number is read from a file you point *HUPy* at via the `ver_grep` setting; if it isn't configured, the header is just `Stable Release` with no number.

See [`.hupy.config.json` Documentation](hupy_config_doc.md#ver_grep) to set it up.


<!-- FIXME merge into cbm -->