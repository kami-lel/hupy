# Installation Documentation

## Install Python Package

#### Clone and Install Locally

```bash
git clone https://github.com/kami-lel/hupy.git
cd hupy
pip install .
```

#### Install Directly from GitHub

```bash
pip install git+https://github.com/kami-lel/hupy.git
```

#### Add as a Project Dependency

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













## Set Up for Repository

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
