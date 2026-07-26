"""
vg-check-version-uniformity_test.py

tests for `check_version_uniformity` in `version_uniformity.py`
"""

from unittest import mock

import git
import pytest

from config_fixture import load_config_fixture

from hupy.state.state_file import HupyStateFile
from hupy.ver_grep.version_uniformity import check_version_uniformity

_STATE_FILE = HupyStateFile()
_REF = "HEAD"

_CANONICAL = {"file": "pyproject.toml", "glob": r'version = "(.*)"'}


# auxiliaries  #################################################################


def _make_repo(repo_dir, files):
    """
    init a plain git repo at ``repo_dir`` with one commit adding every
    ``{filename: content}`` pair in ``files``.
    """
    repo_dir.mkdir(parents=True, exist_ok=True)
    repo = git.Repo.init(str(repo_dir))
    for filename, content in files.items():
        path = repo_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    repo.index.add(list(files))
    repo.index.commit("initial commit")
    return repo


def _check(
    repo,
    occurrences,
    disable_version_uniformity=False,
    allow_version_uniformity_failure=False,
    is_report_only=False,
    ref=_REF,
):
    """
    run ``check_version_uniformity`` against a stubbed config carrying
    ``occurrences``, bypassing disk/git config loading.
    """
    config = load_config_fixture(
        overrides={
            "vg": {
                "version_occurrences": occurrences,
                "disable_version_uniformity": disable_version_uniformity,
                "allow_version_uniformity_failure": (
                    allow_version_uniformity_failure
                ),
            }
        }
    )
    with mock.patch(
        "hupy.should_run_module.load_hupy_config", return_value=config
    ), mock.patch(
        "hupy.ver_grep.version_uniformity.load_hupy_config",
        return_value=config,
    ), mock.patch(
        "hupy.ver_grep.ver_grep.load_hupy_config", return_value=config
    ):
        return check_version_uniformity(
            repo, _STATE_FILE, ref, is_report_only=is_report_only
        )


# tests  ########################################################################


class TestVersionUniformityPass:
    def test_all_occurrences_uniform_does_not_raise(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "badge: version-1.2.3-blue\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
        ]
        assert _check(repo, occurrences) is None


class TestVersionUniformitySkip:
    def test_fewer_than_two_occurrences_does_not_raise(self, repo_dir):
        repo = _make_repo(repo_dir, {"pyproject.toml": 'version = "1.2.3"\n'})
        assert _check(repo, [_CANONICAL]) is None

    def test_empty_occurrences_does_not_raise(self, repo_dir):
        repo = _make_repo(repo_dir, {"pyproject.toml": 'version = "1.2.3"\n'})
        assert _check(repo, []) is None

    def test_disabled_does_not_raise_despite_drift(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "badge: version-9.9.9-blue\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
        ]
        assert (
            _check(repo, occurrences, disable_version_uniformity=True)
            is None
        )

    def test_unreadable_canonical_does_not_raise(self, repo_dir):
        # canonical file never committed; nothing to compare against
        repo = _make_repo(repo_dir, {"README.md": "placeholder\n"})
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"placeholder"},
        ]
        assert _check(repo, occurrences) is None


class TestVersionUniformityFail:
    def test_drifted_occurrence_raises_system_exit(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "badge: version-9.9.9-blue\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
        ]
        with pytest.raises(SystemExit) as exc_info:
            _check(repo, occurrences)
        assert exc_info.value.code == 1

    def test_missing_occurrence_file_raises_system_exit(self, repo_dir):
        repo = _make_repo(repo_dir, {"pyproject.toml": 'version = "1.2.3"\n'})
        occurrences = [
            _CANONICAL,
            {"file": "MISSING.md", "glob": r"version-(\S+)-blue"},
        ]
        with pytest.raises(SystemExit):
            _check(repo, occurrences)

    def test_no_matching_line_raises_system_exit(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "no badge here\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
        ]
        with pytest.raises(SystemExit):
            _check(repo, occurrences)

    def test_multiple_drifted_occurrences_raise_once(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "badge: version-9.9.9-blue\n",
                "docs/index.md": "current: version-8.8.8-page\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
            {"file": "docs/index.md", "glob": r"version-(\S+)-page"},
        ]
        with pytest.raises(SystemExit) as exc_info:
            _check(repo, occurrences)
        assert exc_info.value.code == 1


class TestVersionUniformitySoftFailure:
    def test_allow_failure_downgrades_to_warning(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "badge: version-9.9.9-blue\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
        ]
        assert (
            _check(repo, occurrences, allow_version_uniformity_failure=True)
            is None
        )

    def test_report_only_downgrades_to_warning(self, repo_dir):
        repo = _make_repo(
            repo_dir,
            {
                "pyproject.toml": 'version = "1.2.3"\n',
                "README.md": "badge: version-9.9.9-blue\n",
            },
        )
        occurrences = [
            _CANONICAL,
            {"file": "README.md", "glob": r"version-(\S+)-blue"},
        ]
        assert _check(repo, occurrences, is_report_only=True) is None
