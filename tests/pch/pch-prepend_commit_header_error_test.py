"""
pch-prepend_commit_header_error_test.py

tests for error handling in `prepend_commit_header`: bad repo paths,
a missing COMMIT_EDITMSG, and a failed atomic write
"""

from unittest import mock

import git
import pytest

from hupy.pch import prepend_commit_header
from pch_helpers import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
)
from prep_repo import prepare_repo_with_files


# helpers  ######################################################################


def _prepare_feature_finish(repo_dir):
    prepare_repo_with_files(
        repo_dir, "feature_finish", {"feature.py": "tt_none.py"}
    )


# tests  ########################################################################


class TestPrependCommitHeaderErrors:
    def test_nonexistent_repo_path_raises(self, tmp_path):
        with pytest.raises(git.NoSuchPathError):
            prepend_commit_header(str(tmp_path / "does_not_exist"))

    def test_missing_commit_editmsg_raises_file_not_found(self, repo_dir):
        _prepare_feature_finish(repo_dir)
        # COMMIT_EDITMSG intentionally left unseeded

        with pytest.raises(FileNotFoundError):
            prepend_commit_header(str(repo_dir))

    def test_atomic_write_failure_leaves_original_untouched(self, repo_dir):
        _prepare_feature_finish(repo_dir)
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        with mock.patch(
            "hupy.pch.prepend_commit_header.os.replace",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(OSError):
                prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == original
        assert stray_temp_files(repo_dir) == []
