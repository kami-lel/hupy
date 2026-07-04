"""
setup-parser_configure_hooks_path_test.py

tests for `_configure_repo_hooks_path`: successful config write, and
the failure path when the git config cannot be written
"""

import git
import pytest

from hupy.setup.parser import _configure_repo_hooks_path


# tests  ########################################################################


class TestConfigureHooksPathSuccess:
    def test_sets_core_hooks_path(self, git_repo_dir):
        repo = git.Repo(str(git_repo_dir))
        hooks_dir = git_repo_dir / "scripts" / "hupy-hooks"

        _configure_repo_hooks_path(repo, hooks_dir)

        with repo.config_reader() as reader:
            assert reader.get_value("core", "hooksPath") == str(hooks_dir)


class TestConfigureHooksPathFailure:
    def test_config_write_failure_raises_system_exit(self, tmp_path):
        class _BrokenRepo:
            def config_writer(self):
                raise OSError("disk full")

        with pytest.raises(SystemExit) as exc_info:
            _configure_repo_hooks_path(_BrokenRepo(), tmp_path / "hooks")

        assert exc_info.value.code == 1
