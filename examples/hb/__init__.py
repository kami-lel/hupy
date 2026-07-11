"""
__init__.py

shared helpers for the examples/hb demo scripts: preparing a
temporary HB demo repo with a custom hook-bracket config, and running
`perform_hook_brackets` against it
"""

import pathlib
import sys
import tempfile

import git

_PKG_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from config_fixture import load_config_fixture  # noqa: E402
from hupy.config_file import CONFIG_LOGGER_NAME  # noqa: E402
from hupy.config_file.config_file_path import get_config_file_path  # noqa: E402
from hupy.hb import perform_hook_brackets  # noqa: E402
from hupy.kamilog import set_logging_level_by_verbosity  # noqa: E402
from hupy.state.state_file import HupyStateFile  # noqa: E402
from prep_repo import prepare_repo_with_files as _prepare_bucket_repo  # noqa: E402

_BUCKET = "non_merge_commit"
_FILES = {"a.py": "tt_none.py"}

# the shipped default config leaves `vg` unconfigured, which warns on
# every validation; that warning is noise here, since these demos
# exercise `hb`, not `vg`
set_logging_level_by_verbosity(-2, logger_name=CONFIG_LOGGER_NAME)


# Public API  ##################################################################


def prepare_demo_repo(hb_overrides):
    """
    clone the shared bundle with a plain non-merge commit staged, and
    overwrite its HUPy config file so ``hb`` carries ``hb_overrides``.


    :param hb_overrides: partial ``hb`` config section to deep-merge
            over the shipped default (eg. ``{"pre_commit": {"lead":
            [...]}}``)
    :type hb_overrides: dict
    :return: path to the prepared repository
    :rtype: str
    """
    dest_dir = tempfile.mkdtemp(prefix="hb_demo_")
    repo_dir = _prepare_bucket_repo(dest_dir, _BUCKET, _FILES)

    config = load_config_fixture(overrides={"hb": hb_overrides})
    repo = git.Repo(repo_dir)
    get_config_file_path(repo).write_text(config.model_dump_json(indent=2))

    return repo_dir


def run_hb(repo_dir, hook_name, is_lead, verbosity=1):
    set_logging_level_by_verbosity(verbosity)
    repo = git.Repo(repo_dir, search_parent_directories=True)
    try:
        perform_hook_brackets(repo, HupyStateFile(), hook_name, is_lead)
    except SystemExit:
        pass
