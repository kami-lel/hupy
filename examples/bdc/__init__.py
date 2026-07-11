"""
__init__.py

shared helpers for the examples/bdc demo scripts: preparing a
temporary BDC demo repo (either from a CBM commit-type bucket, or a
fresh unprotected branch with a direct commit) and running
`ban_direct_commit` against it
"""

import os
import pathlib
import shutil
import sys
import tempfile

import git

_PKG_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.bdc import BDC_LOGGER_NAME, ban_direct_commit  # noqa: E402
from hupy.kamilog import set_logging_level_by_verbosity  # noqa: E402
from hupy.state.state_file import HupyStateFile  # noqa: E402
from prep_repo import (  # noqa: E402
    MAIN_BRANCH,
    prepare_repo_with_files as _prepare_bucket_repo,
)

_BUNDLE_PATH = _REPO_ROOT / "tests" / "fixtures" / "default_repo.bundle"
_FIXTURES_ROOT = _REPO_ROOT / "tests" / "ttg" / "fixtures"


# Public API  ##################################################################


def prepare_demo_repo_by_bucket(commit_bucket, files):
    dest_dir = tempfile.mkdtemp(prefix="bdc_demo_")
    return _prepare_bucket_repo(dest_dir, commit_bucket, files)


def prepare_demo_repo_on_branch(branch_name, filename, fixture_name="tt_none.py"):
    """
    clone the shared bundle, check out a fresh, unprotected branch,
    and commit one file directly on it — a non-merge commit
    ``ban_direct_commit`` must never treat as protected
    """
    dest_dir = tempfile.mkdtemp(prefix="bdc_demo_")
    git.Repo.clone_from(str(_BUNDLE_PATH), dest_dir, branch=MAIN_BRANCH)
    # HUPy resolves ``vg.version_file`` against the process cwd,
    # so the bundled setup.cfg must be found from inside the repo
    os.chdir(dest_dir)
    repo = git.Repo(dest_dir)
    repo.git.checkout("-q", "-b", branch_name)

    src = _FIXTURES_ROOT / fixture_name
    dst = pathlib.Path(dest_dir) / filename
    shutil.copyfile(src, dst)
    repo.index.add([filename])
    repo.index.commit("add {}".format(filename))

    return dest_dir


def run_bdc(repo_dir, verbosity=1):
    set_logging_level_by_verbosity(verbosity, logger_name=BDC_LOGGER_NAME)
    repo = git.Repo(repo_dir, search_parent_directories=True)
    try:
        ban_direct_commit(repo, HupyStateFile())
    except SystemExit:
        pass
