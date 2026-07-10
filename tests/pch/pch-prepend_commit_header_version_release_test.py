"""
pch-prepend_commit_header_version_release_test.py

tests for `prepend_commit_header` on Version Release merges; message
formatting internals are already exercised in detail by the Feature
Finish scenario tests, so this file only confirms header selection,
the basic rewrite, and the version-number suffix drawn from ver_grep
"""

from unittest import mock

import git

from hupy.pch import prepend_commit_header
from pch_helpers import (
    read_commit_editmsg,
    seed_commit_editmsg_from_merge_msg,
    stray_temp_files,
    write_commit_editmsg,
)
from prep_repo import prepare_repo_with_files

_BUCKET = "version_release"


# helpers  ######################################################################


def _prepare(repo_dir):
    prepare_repo_with_files(repo_dir, _BUCKET, {"feature.py": "tt_none.py"})
    return git.Repo(str(repo_dir))


def _patch_version(value):
    """stub ``grep_source_branch_version`` to return ``value``."""
    return mock.patch(
        "hupy.pch.prepend_commit_header.grep_source_branch_version",
        return_value=value,
    )


# tests  ########################################################################


class TestVersionReleaseHeaderNoVersion:
    _HEADER = "Version Release"

    def test_real_merge_message_gets_header_prepended(self, repo_dir):
        repo = _prepare(repo_dir)
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        with _patch_version(""):
            prepend_commit_header(repo)

        result = read_commit_editmsg(repo_dir)
        assert result.startswith(self._HEADER + "\n\n")
        assert original.strip() in result

    def test_no_stray_temp_file_left_behind(self, repo_dir):
        repo = _prepare(repo_dir)
        seed_commit_editmsg_from_merge_msg(repo_dir)

        with _patch_version(""):
            prepend_commit_header(repo)

        assert stray_temp_files(repo_dir) == []

    def test_exact_byte_layout_for_simple_message(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version(""):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            self._HEADER + "\n\nsubject only\n"
        )


class TestVersionReleaseHeaderWithVersion:
    """no bump: mocked source (``1.2.3``) equals the real target
    branch's ``setup.cfg`` version"""

    _VERSION = "1.2.3"
    _HEADER = "Stable Release: 1.2.3"

    def test_version_number_is_appended_to_header(self, repo_dir):
        repo = _prepare(repo_dir)
        seed_commit_editmsg_from_merge_msg(repo_dir)
        original = read_commit_editmsg(repo_dir)

        with _patch_version(self._VERSION):
            prepend_commit_header(repo)

        result = read_commit_editmsg(repo_dir)
        assert result.startswith(self._HEADER + "\n\n")
        assert original.strip() in result

    def test_exact_byte_layout_for_simple_message(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version(self._VERSION):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            self._HEADER + "\n\nsubject only\n"
        )

    def test_non_semver_version_string_is_used_verbatim(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("v2024.07-rc1"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Stable Release: v2024.07-rc1\n\nsubject only\n"
        )


class TestVersionReleaseHeaderReleaseType:
    """release-type word, driven by the mocked source version alone;
    the real target branch's ``1.2.3`` never triggers a bump here"""

    def test_alpha_pre_release(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("1.2.3-alpha.1"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Alpha Release: 1.2.3-alpha.1\n\nsubject only\n"
        )

    def test_beta_pre_release(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("1.2.3-beta.1"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Beta Release: 1.2.3-beta.1\n\nsubject only\n"
        )

    def test_zero_major_is_prototype(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("0.3.2"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Prototype Release: 0.3.2\n\nsubject only\n"
        )


class TestVersionReleaseHeaderBumpPrefix:
    """bump prefix, driven by comparing the mocked source version
    against the real target branch's ``1.2.3`` (see prep_repo.py's
    version_release bucket)"""

    def test_major_bump(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("2.0.0"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Major Stable Release: 2.0.0\n\nsubject only\n"
        )

    def test_minor_bump(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("1.3.0"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Minor Stable Release: 1.3.0\n\nsubject only\n"
        )

    def test_patch_bump(self, repo_dir):
        repo = _prepare(repo_dir)
        write_commit_editmsg(repo_dir, "subject only\n")

        with _patch_version("1.2.4"):
            prepend_commit_header(repo)

        assert read_commit_editmsg(repo_dir) == (
            "Patch Stable Release: 1.2.4\n\nsubject only\n"
        )
