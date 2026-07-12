"""
stub-update_stubs_install_hook_stubs_test.py

tests for `install_hook_stubs`: fresh dir, pre-existing but
unrelated dir contents, per-file conflict abort without --force,
override with --force, baking the interpreter path into installed
stubs, only by-demand hook names get installed
"""

import os
import sys

import pytest

from hupy.stub.update_stubs import install_hook_stubs

# helpers  ######################################################################


def _assert_installed(hooks_dir, stub_names):
    for name in stub_names:
        content = (hooks_dir / name).read_text(encoding="utf-8")
        assert content.startswith("#!/usr/bin/env bash\n")
        assert sys.executable in content
        assert "-m hupy hook {}".format(name) in content


# tests  ########################################################################


class TestInstallHookStubsFreshDir:
    def test_creates_missing_dir_and_installs_demanded_stubs(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"

        install_hook_stubs(hooks_dir, repo, force=False)

        assert hooks_dir.is_dir()
        assert sorted(p.name for p in hooks_dir.iterdir()) == stub_names
        _assert_installed(hooks_dir, stub_names)

    def test_installed_stubs_are_executable(self, tmp_path, repo, stub_names):
        hooks_dir = tmp_path / "hooks"

        install_hook_stubs(hooks_dir, repo, force=False)

        for name in stub_names:
            assert os.access(str(hooks_dir / name), os.X_OK)


class TestInstallHookStubsInterpreterPath:
    def test_baked_interpreter_is_an_absolute_path(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"

        install_hook_stubs(hooks_dir, repo, force=False)

        for name in stub_names:
            content = (hooks_dir / name).read_text(encoding="utf-8")
            assert '"{}"'.format(sys.executable) in content
        assert os.path.isabs(sys.executable)


class TestInstallHookStubsPreExistingDir:
    def test_unrelated_dir_contents_do_not_require_force(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        install_hook_stubs(hooks_dir, repo, force=False)

        assert sample.read_text() == "git's own sample hook"
        _assert_installed(hooks_dir, stub_names)


class TestInstallHookStubsConflict:
    def test_without_force_raises_and_leaves_stubs_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in stub_names:
            (hooks_dir / name).write_text("stale content")

        with pytest.raises(SystemExit) as exc_info:
            install_hook_stubs(hooks_dir, repo, force=False)

        assert exc_info.value.code == 1
        for name in stub_names:
            assert (hooks_dir / name).read_text() == "stale content"

    def test_with_force_overrides_stale_content(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in stub_names:
            (hooks_dir / name).write_text("stale content")

        install_hook_stubs(hooks_dir, repo, force=True)

        _assert_installed(hooks_dir, stub_names)
