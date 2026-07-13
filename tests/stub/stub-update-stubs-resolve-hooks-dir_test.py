"""
stub-update-stubs-resolve-hooks-dir_test.py

tests for `resolve_hooks_dir`: defaults to .git/hooks when
core.hooksPath is unset, and honors core.hooksPath (relative and
absolute) when configured
"""

import pathlib

from hupy.stub.update_stubs import resolve_hooks_dir

# tests  ########################################################################


class TestResolveHooksDirDefault:
    def test_defaults_to_dot_git_hooks(self, repo):
        hooks_dir = resolve_hooks_dir(repo)

        assert hooks_dir == pathlib.Path(repo.git_dir) / "hooks"


class TestResolveHooksDirConfigured:
    def test_honors_relative_core_hooks_path(self, repo):
        with repo.config_writer() as writer:
            writer.set_value("core", "hooksPath", "custom-hooks")

        hooks_dir = resolve_hooks_dir(repo)

        assert hooks_dir == pathlib.Path(repo.working_tree_dir) / "custom-hooks"

    def test_honors_absolute_core_hooks_path(self, repo, tmp_path):
        absolute_hooks_dir = tmp_path / "elsewhere" / "hooks"
        with repo.config_writer() as writer:
            writer.set_value("core", "hooksPath", str(absolute_hooks_dir))

        hooks_dir = resolve_hooks_dir(repo)

        assert hooks_dir == absolute_hooks_dir
