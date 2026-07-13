"""
pch-feature-landing_test.py

tests for `prepend_commit_header` on Feature Landing merges, covering
the header content and the COMMIT_EDITMSG rewrite behavior in detail
"""

from hupy.pch import prepend_commit_header
from hupy.state.state_file import HupyStateFile
from . import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
    write_commit_editmsg,
)

_STATE_FILE = HupyStateFile()

_HEADER = "Feature Landing: add-user-authentication"


# tests  ########################################################################


class TestFeatureFinishHeaderContent:
    def test_real_merge_message_gets_header_prepended(
        self, repo_dir, feature_landing_repo
    ):
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        result = read_commit_editmsg(repo_dir)
        assert result.startswith(_HEADER + "\n\n")
        assert original.strip() in result

    def test_no_stray_temp_file_left_behind(
        self, repo_dir, feature_landing_repo
    ):
        seed_commit_editmsg_from_merge_msg(repo_dir)

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert stray_temp_files(repo_dir) == []


class TestFeatureFinishMessageFormatting:
    def test_comment_lines_are_regrouped_after_content(
        self, repo_dir, feature_landing_repo
    ):
        write_commit_editmsg(
            repo_dir,
            "subject line\n"
            "# comment 1\n"
            "body line\n"
            "   # comment 2 with leading whitespace\n",
        )

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            _HEADER + "\n"
            "\n"
            "subject line\n"
            "body line\n"
            "# comment 1\n"
            "   # comment 2 with leading whitespace"
        )

    def test_all_comment_message_collapses_to_header_only(
        self, repo_dir, feature_landing_repo
    ):
        write_commit_editmsg(repo_dir, "# only a comment\n")

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            _HEADER + "\n\n# only a comment"
        )

    def test_no_comment_message_has_no_comment_block(
        self, repo_dir, feature_landing_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == _HEADER + "\n\nsubject only\n"

    def test_empty_commit_message_does_not_crash(
        self, repo_dir, feature_landing_repo
    ):
        write_commit_editmsg(repo_dir, "")

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == _HEADER + "\n\n"

    def test_non_ascii_content_round_trips(
        self, repo_dir, feature_landing_repo
    ):
        write_commit_editmsg(repo_dir, "fix: 修复 bug 🐛\n")

        prepend_commit_header(feature_landing_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            _HEADER + "\n\nfix: 修复 bug 🐛\n"
        )
