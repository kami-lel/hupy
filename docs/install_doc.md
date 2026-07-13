# Installation Documentation

<!--
TODO doc for using pyproject.toml & setup.cfg
-->

### Install Python Package

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



### Set Up for Repository

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
