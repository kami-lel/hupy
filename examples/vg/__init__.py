"""
__init__.py

shared helpers for the examples/vg demo scripts: preparing a
temporary repo with a HUPy config carrying a caller-chosen
`version_file`/`version_line_pattern`, optionally committing that
version file, and running `grep_version` against it
"""

import json
import pathlib
import sys
import tempfile

import git
import json5

_PKG_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.config_file.config_file_path import (  # noqa: E402
    CONFIG_FILENAME,
    DEFAULT_CONFIG_ASSET,
)
from hupy.kamilog import set_logging_level_by_verbosity  # noqa: E402
from hupy.state.state_file import HupyStateFile  # noqa: E402
from hupy.ver_grep import VER_GREP_LOGGER_NAME  # noqa: E402
from hupy.ver_grep.ver_grep import grep_version  # noqa: E402
from hupy.ver_grep.version_uniformity import check_version_uniformity  # noqa: E402

_STATE_FILE = HupyStateFile()


# auxiliaries  #################################################################


def _write_config_file(dest_dir, version_file, version_line_pattern):
    config = json5.loads(DEFAULT_CONFIG_ASSET.read_text())
    config["vg"]["version_occurrences"] = (
        []
        if not version_file and not version_line_pattern
        else [{"file": version_file, "glob": version_line_pattern}]
    )
    (pathlib.Path(dest_dir) / CONFIG_FILENAME).write_text(json.dumps(config))


# Public API  ##################################################################


def prepare_demo_repo(
    version_file="VERSION",
    version_line_pattern=r"(\d+\.\d+\.\d+)",
    version_content=None,
):
    """
    init a fresh repo with an initial commit, a HUPy config carrying
    `version_file`/`version_line_pattern`, and `version_file`
    committed with `version_content` on top when given.
    """
    dest_dir = tempfile.mkdtemp(prefix="vg_demo_")
    repo = git.Repo.init(dest_dir)
    _write_config_file(dest_dir, version_file, version_line_pattern)

    readme = pathlib.Path(dest_dir) / "README.md"
    readme.write_text("placeholder\n")
    repo.index.add(["README.md"])
    repo.index.commit("initial commit")

    if version_content is not None:
        version_path = pathlib.Path(dest_dir) / version_file
        version_path.write_text(version_content)
        repo.index.add([version_file])
        repo.index.commit("add {}".format(version_file))

    return dest_dir


def run_vg(repo_dir, ref="HEAD", verbosity=1):
    set_logging_level_by_verbosity(verbosity, logger_name=VER_GREP_LOGGER_NAME)
    repo = git.Repo(repo_dir, search_parent_directories=True)
    return grep_version(repo, _STATE_FILE, ref)


def prepare_uniformity_demo_repo(
    occurrences,
    files,
    disable_version_uniformity=False,
    allow_version_uniformity_failure=False,
):
    """
    init a fresh repo with a HUPy config carrying `occurrences` as
    `vg.version_occurrences`, and every `{filename: content}` pair in
    `files` committed in one initial commit.
    """
    dest_dir = tempfile.mkdtemp(prefix="vg_uniformity_demo_")
    repo = git.Repo.init(dest_dir)

    config = json5.loads(DEFAULT_CONFIG_ASSET.read_text())
    config["vg"]["version_occurrences"] = occurrences
    config["vg"]["disable_version_uniformity"] = disable_version_uniformity
    config["vg"]["allow_version_uniformity_failure"] = (
        allow_version_uniformity_failure
    )
    (pathlib.Path(dest_dir) / CONFIG_FILENAME).write_text(json.dumps(config))

    for filename, content in files.items():
        path = pathlib.Path(dest_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    repo.index.add(list(files))
    repo.index.commit("initial commit")

    return dest_dir


def run_uniformity(repo_dir, ref="HEAD", verbosity=1):
    set_logging_level_by_verbosity(verbosity, logger_name=VER_GREP_LOGGER_NAME)
    repo = git.Repo(repo_dir, search_parent_directories=True)
    check_version_uniformity(repo, _STATE_FILE, ref)
