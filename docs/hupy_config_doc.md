# HUPy File `.hupy.config.json` Documentation

`.hupy.config.json` is *HUPy*'s per-repository config. `python -m hupy init` writes it to the repository root; commit it so every clone shares the same behavior.

## Fields

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
