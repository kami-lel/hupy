"""
vg-verify_version_grep_test.py

tests for `verify_version_grep` in `branch_version.py`; it greps the
working tree standalone and only warns, never exits
"""

from unittest import mock

import git

from config_fixture import load_config_fixture

from hupy.ver_grep import verify_version_grep

_VERSION_FILE = "VERSION"
_PATTERN = r"(\d+\.\d+\.\d+)"


# helpers  ######################################################################


def _make_repo(repo_dir, version_content=None, version_file=_VERSION_FILE):
    """
    init a git repo at ``repo_dir``, optionally writing ``version_file``
    into its working tree with ``version_content``.
    """
    repo_dir.mkdir(parents=True, exist_ok=True)
    repo = git.Repo.init(str(repo_dir))
    if version_content is not None:
        (repo_dir / version_file).write_text(version_content)
    return repo


def _verify(repo, pattern=_PATTERN, version_file=_VERSION_FILE, disabled=False):
    """
    run ``verify_version_grep`` against a stubbed config carrying
    ``version_file``, ``pattern``, and ``is_disabled``, bypassing
    disk/git config loading; returns the mocked module logger for
    call assertions.
    """
    config = load_config_fixture(
        overrides={
            "vg": {
                "is_disabled": disabled,
                "version_file": version_file,
                "version_line_pattern": pattern,
            }
        }
    )
    with mock.patch(
        "hupy.ver_grep.branch_version.load_hupy_config", return_value=config
    ), mock.patch("hupy.ver_grep.branch_version.logger") as logger:
        verify_version_grep(repo)
    return logger


# tests  ########################################################################


class TestVerifyVersionGrep:
    def test_valid_config_passes(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        logger = _verify(repo)
        logger.pass_.assert_called_once()
        logger.warning.assert_not_called()

    def test_disabled_skips(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        logger = _verify(repo, disabled=True)
        logger.skip.assert_called_once()
        logger.pass_.assert_not_called()

    def test_missing_version_file_warns(self, repo_dir):
        repo = _make_repo(repo_dir)  # no version file written
        logger = _verify(repo)
        logger.warning.assert_called_once()
        logger.pass_.assert_not_called()

    def test_no_matching_line_warns(self, repo_dir):
        repo = _make_repo(repo_dir, "unreleased\n")
        logger = _verify(repo)
        logger.warning.assert_called_once()
        logger.pass_.assert_not_called()

    def test_pattern_without_capture_group_warns(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        logger = _verify(repo, pattern=r"\d+\.\d+\.\d+")
        logger.warning.assert_called_once()
        logger.pass_.assert_not_called()
