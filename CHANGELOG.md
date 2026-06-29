# hupy CHANGELOG

[^format]















## [Unreleased]

### Added

- `pyproject.toml` — pip-installable `hupy` package using `setuptools.build_meta`
- `hupy/__init__.py` — package entry point
- `AGENTS.md` — agent behavioral instructions: setup commands, code style, testing, and PR rules
- `CONTEXT.md` — architecture overview, module responsibility table, and annotation marker tiers
- `.gitignore` — Python bytecode, build artifacts, venv dirs, and local agent override files

### Changed

- rewrote `README.md` with structured sections: features, tech stack, project layout, build and test, acknowledgments

### Deprecated

### Removed

### Fixed

- build backend corrected from `setuptools.backends.legacy:build` to `setuptools.build_meta`

### Security

[unreleased]: https://github.com/kami-lel/hooks-utility-py/compare/v0.1.0...dev













[^format]: CHANGELOG format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); Version scheme adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
