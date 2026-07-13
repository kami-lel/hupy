"""
pch-error_test.py

tests for error handling in `prepend_commit_header`: bad repo paths,
a missing COMMIT_EDITMSG, and a failed atomic write
"""

from unittest import mock

import git
import pytest

from hupy.pch import prepend_commit_header
from hupy.state.state_file import HupyStateFile
from . import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
)

_STATE_FILE = HupyStateFile()


# tests  ########################################################################


class TestPrependCommitHeaderErrors:
    def test_nonexistent_repo_path_raises(self, tmp_path):
        # repo construction is now the caller's responsibility; a bad
        # path must fail there, before prepend_commit_header is ever
        # reached
        with pytest.raises(git.NoSuchPathError):
            git.Repo(
                str(tmp_path / "does_not_exist"),
                search_parent_directories=True,
            )

    def test_missing_commit_editmsg_raises_file_not_found(
        self, feature_landing_repo
    ):
        # COMMIT_EDITMSG intentionally left unseeded
        with pytest.raises(FileNotFoundError):
            prepend_commit_header(feature_landing_repo, _STATE_FILE)

    def test_atomic_write_failure_leaves_original_untouched(
        self, repo_dir, feature_landing_repo
    ):
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        with mock.patch(
            "hupy.pch.prepend_commit_header.os.replace",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(OSError):
                prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == original
        assert stray_temp_files(repo_dir) == []
