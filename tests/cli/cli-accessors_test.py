"""
cli-accessors_test.py

tests for the ``branch-type`` accessor key's ``run_get`` in
`cli/accessors/branch_type.py`
"""

import git
import pytest
from prep_repo import prepare_repo_with_files

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cbm.branch_type import BranchType
from hupy.cli.accessors import branch_type

logger = kamilog.getLogger(PROJ_LOGGER_NAME)

_DEFAULT_FILES = {"a.py": "tt_none.py"}


def _clone_repo(repo_dir):
    """clone the plain default_repo bundle, no merge in progress."""
    prepare_repo_with_files(repo_dir, "non_merge_commit", _DEFAULT_FILES)
    repo = git.Repo(str(repo_dir))
    repo.git.reset("-q", "--hard", "HEAD")  # drop the staged default file
    return repo


# tests  ########################################################################


class TestBranchTypeRunGet:
    @pytest.mark.parametrize(
        "branch_name,expected",
        [
            ("main", BranchType.MAIN),
            ("dev", BranchType.DEV),
            ("add-user-authentication", BranchType.FEATURE),
            ("hotfix/fix-login-crash", BranchType.HOTFIX),
            ("release/1.3.0", BranchType.RELEASE),
            ("kami/scratch-branch", BranchType.USER),
        ],
    )
    def test_prints_branch_type_name(
        self, repo_dir, capsys, branch_name, expected
    ):
        repo = _clone_repo(repo_dir)
        if branch_name != "main":
            repo.git.checkout("-q", "-b", branch_name)

        branch_type.run_get(repo, None, logger, None)

        assert capsys.readouterr().out.strip() == expected.name

    def test_detached_head_raises(self, repo_dir):
        repo = _clone_repo(repo_dir)
        repo.git.checkout("-q", repo.head.commit.hexsha)

        with pytest.raises(SystemExit):
            branch_type.run_get(repo, None, logger, None)
