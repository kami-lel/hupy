"""
__init__.py

shared helpers for the examples/pch demo scripts: preparing a
temporary PCH demo repo (from either a legacy scenario name or a
CBM demo bucket) and running `prepend_commit_header` against it
"""

import os
import pathlib
import sys
import tempfile

import git

_PKG_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.kamilog import set_logging_level_by_verbosity  # noqa: E402
from hupy.pch import prepend_commit_header  # noqa: E402
from prep_repo import (  # noqa: E402
    prepare_demo_repo as _prepare_bucket_repo,
    prepare_repo as _prepare_scenario_repo,
)


# Public API  ##################################################################


def prepare_demo_repo_by_scenario(scenario):
    dest_dir = tempfile.mkdtemp(prefix="pch_demo_")
    return _prepare_scenario_repo(dest_dir, scenario)


def prepare_demo_repo_by_bucket(demo_bucket):
    dest_dir = tempfile.mkdtemp(prefix="pch_demo_")
    return _prepare_bucket_repo(dest_dir, demo_bucket)


def run_pch(repo_dir, verbosity=1):
    set_logging_level_by_verbosity(verbosity)
    cwd = os.getcwd()
    os.chdir(repo_dir)
    try:
        repo = git.Repo(repo_dir, search_parent_directories=True)
        prepend_commit_header(repo)
    finally:
        os.chdir(cwd)
