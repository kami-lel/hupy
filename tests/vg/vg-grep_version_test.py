"""
vg-grep_version_test.py

tests for `grep_version` in `ver_grep.py`
"""

from unittest import mock

import git

from config_fixture import load_config_fixture
from prep_repo import _write_config_file

from hupy.state.state_file import HupyStateFile
from hupy.ver_grep.ver_grep import grep_version

_VERSION_FILE = "VERSION"
_PATTERN = r"(\d+\.\d+\.\d+)"
_REF = "HEAD"

_STATE_FILE = HupyStateFile()


# helpers  ######################################################################


def _make_repo(repo_dir, version_content=None, version_file=_VERSION_FILE):
    """
    init a plain (non-merge) git repo at ``repo_dir`` with one initial
    commit, then commit ``version_file`` with ``version_content`` on
    top when given.
    """
    repo_dir.mkdir(parents=True, exist_ok=True)
    repo = git.Repo.init(str(repo_dir))
    _write_config_file(repo_dir)
    (repo_dir / "README.md").write_text("placeholder\n")
    repo.index.add(["README.md"])
    repo.index.commit("initial commit")
    if version_content is not None:
        (repo_dir / version_file).write_text(version_content)
        repo.index.add([version_file])
        repo.index.commit("add {}".format(version_file))
    return repo


def _grep(repo, ref=_REF, pattern=_PATTERN, version_file=_VERSION_FILE):
    """
    run ``grep_version`` against a stubbed config carrying
    ``version_file`` and ``pattern``, bypassing disk/git config
    loading.
    """
    config = load_config_fixture(
        overrides={
            "vg": {
                "version_file": version_file,
                "version_line_pattern": pattern,
            }
        }
    )
    with mock.patch(
        "hupy.ver_grep.ver_grep.load_hupy_config", return_value=config
    ):
        return grep_version(repo, _STATE_FILE, ref)


# tests  ########################################################################


class TestGrepVersionMatch:
    def test_returns_captured_group(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        assert _grep(repo) == "1.2.3"

    def test_returns_first_matching_line(self, repo_dir):
        repo = _make_repo(repo_dir, "1.0.0\n2.0.0\n")
        assert _grep(repo) == "1.0.0"

    def test_custom_pattern_with_capturing_group(self, repo_dir):
        repo = _make_repo(repo_dir, 'version = "4.5.6"\n', "pyproject.toml")
        assert (
            _grep(
                repo,
                pattern=r'version = "(.*)"',
                version_file="pyproject.toml",
            )
            == "4.5.6"
        )

    def test_reads_content_at_given_ref(self, repo_dir):
        repo = _make_repo(repo_dir, "1.0.0\n")
        repo.git.tag("v1")
        (repo_dir / _VERSION_FILE).write_text("2.0.0\n")
        repo.index.add([_VERSION_FILE])
        repo.index.commit("bump to 2.0.0")
        repo.git.tag("v2")

        assert _grep(repo, ref="v1") == "1.0.0"
        assert _grep(repo, ref="v2") == "2.0.0"


class TestGrepVersionNotConfigured:
    def test_default_unconfigured_returns_empty(self, repo_dir):
        # neither `version_file` nor `version_line_pattern` is
        # stubbed, so the shipped default config's empty values apply
        repo = _make_repo(repo_dir, "1.2.3\n")
        assert grep_version(repo, _STATE_FILE, _REF) == ""

    def test_empty_version_file_returns_empty(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        assert _grep(repo, version_file="") == ""

    def test_dot_version_file_returns_empty(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        assert _grep(repo, version_file=".") == ""

    def test_empty_pattern_returns_empty(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        assert _grep(repo, pattern="") == ""


class TestGrepVersionGracefulEmpty:
    def test_missing_version_file_on_ref_returns_empty(self, repo_dir):
        repo = _make_repo(repo_dir)  # no version file committed
        assert _grep(repo) == ""

    def test_no_matching_line_returns_empty(self, repo_dir):
        repo = _make_repo(repo_dir, "unreleased\n")
        assert _grep(repo) == ""

    def test_pattern_without_capture_group_returns_empty(self, repo_dir):
        repo = _make_repo(repo_dir, "1.2.3\n")
        assert _grep(repo, pattern=r"\d+\.\d+\.\d+") == ""
