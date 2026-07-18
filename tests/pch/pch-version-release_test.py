"""
pch-version-release_test.py

tests for `prepend_commit_header` on Version Release merges; message
formatting internals are already exercised in detail by the Feature
Finish scenario tests, so this file only confirms header selection,
the basic rewrite, and the release-type/bump-prefix wording drawn
from ver_grep
"""

from unittest import mock

from hupy.pch import prepend_commit_header
from hupy.state.state_file import HupyStateFile
from . import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
    write_commit_editmsg,
)

_STATE_FILE = HupyStateFile()


# auxiliaries  #################################################################


def _patch_version(value):
    """stub ``grep_source_branch_version`` to return ``value``."""
    return mock.patch(
        "hupy.pch.prepend_commit_header.grep_source_branch_version",
        return_value=value,
    )


def _patch_target_version(value):
    """stub ``grep_target_branch_version`` to return ``value``."""
    return mock.patch(
        "hupy.pch.prepend_commit_header.grep_target_branch_version",
        return_value=value,
    )


# tests  ########################################################################


class TestVersionReleaseHeaderNoVersion:
    _HEADER = "Version Release"

    def test_real_merge_message_gets_header_prepended(
        self, repo_dir, version_release_repo
    ):
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        with _patch_version(""):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        result = read_commit_editmsg(repo_dir)
        assert result.startswith(self._HEADER + "\n\n")
        assert original.strip() in result

    def test_no_stray_temp_file_left_behind(
        self, repo_dir, version_release_repo
    ):
        seed_commit_editmsg_from_merge_msg(repo_dir)

        with _patch_version(""):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert stray_temp_files(repo_dir) == []

    def test_exact_byte_layout_for_simple_message(
        self, repo_dir, version_release_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version(""):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            self._HEADER + "\n\nsubject only\n"
        )


class TestVersionReleaseHeaderWithVersion:
    """no bump: mocked source (``1.2.3``) equals the real target
    branch's ``setup.cfg`` version"""

    _VERSION = "1.2.3"
    _HEADER = "Stable Release: 1.2.3"

    def test_version_number_is_appended_to_header(
        self, repo_dir, version_release_repo
    ):
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        with _patch_version(self._VERSION):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        result = read_commit_editmsg(repo_dir)
        assert result.startswith(self._HEADER + "\n\n")
        assert original.strip() in result

    def test_exact_byte_layout_for_simple_message(
        self, repo_dir, version_release_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version(self._VERSION):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            self._HEADER + "\n\nsubject only\n"
        )


class TestVersionReleaseHeaderScenarios:
    """the seven release-type/bump-prefix combinations pch's
    ``examples/pch/vr-*-demo.py`` scripts also demonstrate
    end-to-end against a real repo"""

    def test_fail_parse_version_falls_back_to_plain_prefix(
        self, repo_dir, version_release_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("v2024.07-nightly"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Version Release: v2024.07-nightly\n\nsubject only\n"
        )

    def test_minor_prototype_release(self, repo_dir, version_release_repo):
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("0.4.0"), _patch_target_version("0.3.0"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Minor Prototype Release: 0.4.0\n\nsubject only\n"
        )

    def test_alpha_release_has_no_bump_prefix(
        self, repo_dir, version_release_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        # target set to a version that would otherwise trigger a
        # major bump, proving alpha releases skip the bump prefix
        with _patch_version("1.3.0-alpha.1"), _patch_target_version("0.9.0"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Alpha Release: 1.3.0-alpha.1\n\nsubject only\n"
        )

    def test_beta_release_has_no_bump_prefix(
        self, repo_dir, version_release_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        # target set to a version that would otherwise trigger a
        # major bump, proving beta releases skip the bump prefix
        with _patch_version("1.3.0-beta.1"), _patch_target_version("0.9.0"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Beta Release: 1.3.0-beta.1\n\nsubject only\n"
        )

    def test_release_candidate_has_no_bump_prefix(
        self, repo_dir, version_release_repo
    ):
        write_commit_editmsg(repo_dir, "subject only\n")

        # target set to a version that would otherwise trigger a
        # major bump, proving RC releases skip the bump prefix
        with _patch_version("1.3.0-rc.1"), _patch_target_version("0.9.0"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Release Candidate: 1.3.0-rc.1\n\nsubject only\n"
        )

    def test_major_stable_release(self, repo_dir, version_release_repo):
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("2.0.0"), _patch_target_version("1.2.3"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Major Stable Release: 2.0.0\n\nsubject only\n"
        )

    def test_minor_pre_alpha_release(self, repo_dir, version_release_repo):
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("0.9.0"), _patch_target_version("0.8.5"):
            prepend_commit_header(version_release_repo, _STATE_FILE)

        assert read_commit_editmsg(repo_dir) == (
            "Minor Pre-Alpha Release: 0.9.0\n\nsubject only\n"
        )
