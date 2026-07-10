"""
__init__.py

shared helpers for the examples/ttg demo scripts: preparing a
temporary TTG demo repo from a commit-type bucket and file manifest,
and running `perform_triage_tags_gating` against it
"""

import pathlib
import sys
import tempfile

import git

_PKG_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.kamilog import set_logging_level_by_verbosity  # noqa: E402
from hupy.ttg import TTG_LOGGER_NAME  # noqa: E402
from hupy.ttg.tt_gating import perform_triage_tags_gating  # noqa: E402
from prep_repo import prepare_repo_with_files  # noqa: E402


# Public API  ##################################################################


def prepare_demo_repo(bucket, files):
    dest_dir = tempfile.mkdtemp(prefix="ttg_demo_")
    return prepare_repo_with_files(dest_dir, bucket, files)


def run_ttg(repo_dir, verbosity=1):
    set_logging_level_by_verbosity(verbosity, logger_name=TTG_LOGGER_NAME)
    repo = git.Repo(repo_dir, search_parent_directories=True)
    try:
        perform_triage_tags_gating(repo)
    except SystemExit:
        pass
