"""
pch-prepend_commit_header_version_release_test.py

tests for `prepend_commit_header` on Version Release merges; message
formatting internals are already exercised in detail by the Feature
Finish scenario tests, so this file only confirms header selection
and the basic rewrite
"""

from hupy.pch import prepend_commit_header
from pch_helpers import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
    write_commit_editmsg,
)
from prep_repo import prepare_repo_with_files

_BUCKET = "version_release"
_HEADER = "Version Release"


# helpers  ######################################################################


def _prepare(repo_dir):
    prepare_repo_with_files(repo_dir, _BUCKET, {"feature.py": "tt_none.py"})


# tests  ########################################################################


class TestVersionReleaseHeaderContent:
    def test_real_merge_message_gets_header_prepended(self, repo_dir):
        _prepare(repo_dir)
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        prepend_commit_header(str(repo_dir))

        result = read_commit_editmsg(repo_dir)
        assert result.startswith(_HEADER + "\n\n")
        assert original.strip() in result

    def test_no_stray_temp_file_left_behind(self, repo_dir):
        _prepare(repo_dir)
        seed_commit_editmsg_from_merge_msg(repo_dir)

        prepend_commit_header(str(repo_dir))

        assert stray_temp_files(repo_dir) == []

    def test_exact_byte_layout_for_simple_message(self, repo_dir):
        _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == _HEADER + "\n\nsubject only\n"
