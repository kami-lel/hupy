"""
pch-prepend_commit_header_feature_finish_test.py

tests for `prepend_commit_header` on Feature Finish merges, covering
the header content and the COMMIT_EDITMSG rewrite behavior in detail
"""

from hupy.pch import prepend_commit_header
from pch_helpers import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
    write_commit_editmsg,
)
from prep_repo import prepare_repo_with_files

_BUCKET = "feature_finish"
_HEADER = "Feature Finish: add-user-authentication"


# helpers  ######################################################################


def _prepare(repo_dir):
    prepare_repo_with_files(repo_dir, _BUCKET, {"feature.py": "tt_none.py"})


# tests  ########################################################################


class TestFeatureFinishHeaderContent:
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


class TestFeatureFinishMessageFormatting:
    def test_comment_lines_are_regrouped_after_content(self, repo_dir):
        _prepare(repo_dir)
        write_commit_editmsg(
            repo_dir,
            "subject line\n"
            "# comment 1\n"
            "body line\n"
            "   # comment 2 with leading whitespace\n",
        )

        prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == (
            _HEADER + "\n"
            "\n"
            "subject line\n"
            "body line\n"
            "# comment 1\n"
            "   # comment 2 with leading whitespace"
        )

    def test_all_comment_message_collapses_to_header_only(self, repo_dir):
        _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "# only a comment\n")

        prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == (
            _HEADER + "\n\n# only a comment"
        )

    def test_no_comment_message_has_no_comment_block(self, repo_dir):
        _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == _HEADER + "\n\nsubject only\n"

    def test_empty_commit_message_does_not_crash(self, repo_dir):
        _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "")

        prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == _HEADER + "\n\n"

    def test_non_ascii_content_round_trips(self, repo_dir):
        _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "fix: 修复 bug 🐛\n")

        prepend_commit_header(str(repo_dir))

        assert read_commit_editmsg(repo_dir) == (
            _HEADER + "\n\nfix: 修复 bug 🐛\n"
        )
