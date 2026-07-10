"""
pch-prepend_commit_header_skip_test.py

tests for `prepend_commit_header` on commit types it must skip:
regular non-merge commits and merges unrelated to Feature Landing or
Version Release
"""

import git

from hupy.pch import prepend_commit_header
from hupy.state.state_file import HupyStateFile
from pch_helpers import read_commit_editmsg, write_commit_editmsg
from prep_repo import prepare_repo_with_files

_STATE_FILE = HupyStateFile()

_SENTINEL = "unrelated commit message\n"


# helpers  ######################################################################


def _assert_skipped(repo_dir, bucket):
    prepare_repo_with_files(repo_dir, bucket, {"feature.py": "tt_none.py"})
    write_commit_editmsg(repo_dir, _SENTINEL)

    prepend_commit_header(git.Repo(str(repo_dir)), _STATE_FILE)

    assert read_commit_editmsg(repo_dir) == _SENTINEL


# tests  ########################################################################


class TestSkipsNonMergeAndIrrelevantMerges:
    def test_non_merge_commit_is_skipped(self, repo_dir):
        _assert_skipped(repo_dir, "non_merge_commit")

    def test_regular_merge_is_skipped(self, repo_dir):
        _assert_skipped(repo_dir, "regular_merge")
