"""
cli-cli_initresolve_hooks_dir_test.py

tests for `resolve_hooks_dir`: defaults to .git/hooks when
core.hooksPath is unset, and honors core.hooksPath (relative and
absolute) when configured
"""

import pathlib

import git

from hupy.cli.cli_init import resolve_hooks_dir


# tests  ########################################################################


class TestResolveHooksDirDefault:
    def test_defaults_to_dot_git_hooks(self, git_repo_dir):
        repo = git.Repo(str(git_repo_dir))

        hooks_dir = resolve_hooks_dir(repo)

        assert hooks_dir == pathlib.Path(repo.git_dir) / "hooks"


class TestResolveHooksDirConfigured:
    def test_honors_relative_core_hooks_path(self, git_repo_dir):
        repo = git.Repo(str(git_repo_dir))
        with repo.config_writer() as writer:
            writer.set_value("core", "hooksPath", "custom-hooks")

        hooks_dir = resolve_hooks_dir(repo)

        assert hooks_dir == git_repo_dir / "custom-hooks"

    def test_honors_absolute_core_hooks_path(self, git_repo_dir, tmp_path):
        repo = git.Repo(str(git_repo_dir))
        absolute_hooks_dir = tmp_path / "elsewhere" / "hooks"
        with repo.config_writer() as writer:
            writer.set_value("core", "hooksPath", str(absolute_hooks_dir))

        hooks_dir = resolve_hooks_dir(repo)

        assert hooks_dir == absolute_hooks_dir
