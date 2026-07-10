# HUPy File `.hupy.config.json` Documentation

<!-- HACK move doc to jsonc  -->

`.hupy.config.json` is *HUPy*'s per-repository config. `python -m hupy init` writes it to the repository root; commit it so every clone shares the same behavior.

```json
{
  "hupy_version": "1.0.0",
  "default_logger_verbosity": 1,
  "ver_grep": {
    "version_file": ".",
    "version_line_pattern": ""
  }
}
```

| Field | Purpose |
|---|---|
| `hupy_version` | *HUPy* version that wrote the file; informational, no need to edit |
| `default_logger_verbosity` | hook log verbosity: `3`+ DEBUG, `2` ENTER, `1` INFO *(default)*, `0` DONE, `-1` WARNING, `-2` ERROR, `-3`- CRITICAL |
| `ver_grep` | how to read the repo's version string — see below |
| `cbm` | branch names/prefixes the *CBM* module (commit, branch, and merge types) classifies against — see below |
| `pch` | how *Prepend Commit Header* understands versions and picks a header — see below |
| `bdc` | branches that *Ban Direct Commit* blocks direct commits to — see below |


































## `ver_grep`

Powers the *Prepend Commit Header* hook: a **Version Release** merge gets the header `Version Release: <version>` when a version resolves, else plain `Version Release`.

| Sub-field | Purpose |
|---|---|
| `version_file` | file to read, relative to the repo root |
| `version_line_pattern` | Python regex whose first capturing group `( )` is the version |

The pattern runs per line (`re.search`); the first matching line wins. Escape any double quote in JSON as `\"`. Empty fields disable `ver_grep`, so the header falls back to plain `Version Release`.













### Common Patterns

| Version file | Example line | `version_line_pattern` (JSON) |
|---|---|---|
| `pyproject.toml` | `version = "1.0.0"` | `"^version = \"(.*)\""` |
| `package.json` | `"version": "1.0.0",` | `"\"version\": \"(.*)\""` |
| `hupy/__init__.py` | `__version__ = "1.0.0"` | `"__version__ = \"(.*)\""` |
| `VERSION` | `1.0.0` | `"(.*)"` |

Anchor with `^` when several `version`-like lines exist.

































## `cbm`

Classifies git branches by naming convention, so *CBM* can decide the merge
type (eg. `feature → dev` is a *Feature Landing*, `hotfix/* → main` is a
*Hotfix Release*). Every branch not matched by a field below, and holding a
`/` in its name, counts as a *User* branch; anything else is a *Feature*
branch.

| Sub-field | Default | Purpose |
|---|---|---|
| `main_branch_name` | `main` | exact name of the main branch |
| `dev_branch_name` | `dev` | exact name of the dev branch |
| `hotfix_branch_prefix` | `hotfix` | prefix (before `/`) marking a hotfix branch |
| `release_branch_prefix` | `release` | prefix (before `/`) marking a release branch |

Each field must be non-empty.


































## `pch`

Configures how *Prepend Commit Header* understands a resolved version and which header it prepends accordingly.

| Sub-field | Default | Purpose |
|---|---|---|
| `enable_vertical_slice` | `false` | enable the *Vertical Slice* header |
| `enable_pre_alpha` | `true` | enable the *Pre-Alpha* header |
| `alpha_tag` | `-alpha` | version suffix identifying an alpha release |
| `beta_tag` | `-beta` | version suffix identifying a beta release |
| `release_candidate_tag` | `-rc` | version suffix identifying a release candidate |

Leave any of `alpha_tag`, `beta_tag`, `release_candidate_tag` empty to disable that tag: *PCH* will no longer recognize that release type and skips its header.




































## `bdc`

Configures *Ban Direct Commit*: blocks a commit made directly on a protected
branch, while still allowing that branch to receive commits through a
merge (eg. `feature → dev`, `dev → main`). Only the direct-commit path is
blocked; merging is unaffected.

| Sub-field | Default |
|---|---|
| `ban_commit_to_dev` | `false` |
| `ban_commit_to_main` | `true` |
| `ban_commit_to_branches` | `[]` |

`ban_commit_to_branches` is a list of branch names, matched exactly, that
must not be directly committed to, on top of whatever
`ban_commit_to_dev`/`ban_commit_to_main` already cover.
