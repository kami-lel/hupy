"""
stub-update_stubs_create_init_hook_stubs_test.py

tests for `create_init_hook_stubs`: fresh dir, pre-existing but
unrelated dir contents, per-file conflict abort without --force,
override with --force, baking the interpreter path into installed
stubs, only by-demand hook names get installed
"""

import os
import sys

import pytest

from hupy.stub.names_by_demand import get_hook_names_by_demand
from hupy.stub.update_stubs import create_init_hook_stubs

_STUB_NAMES = sorted(get_hook_names_by_demand())


# helpers  ######################################################################


def _assert_installed(hooks_dir):
    for name in _STUB_NAMES:
        content = (hooks_dir / name).read_text(encoding="utf-8")
        assert content.startswith("#!/usr/bin/env bash\n")
        assert sys.executable in content
        assert "-m hupy hook {}".format(name) in content


# tests  ########################################################################


class TestCreateInitHookStubsFreshDir:
    def test_creates_missing_dir_and_installs_demanded_stubs(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        create_init_hook_stubs(hooks_dir, force=False)

        assert hooks_dir.is_dir()
        assert sorted(p.name for p in hooks_dir.iterdir()) == _STUB_NAMES
        _assert_installed(hooks_dir)

    def test_installed_stubs_are_executable(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        create_init_hook_stubs(hooks_dir, force=False)

        for name in _STUB_NAMES:
            assert os.access(str(hooks_dir / name), os.X_OK)


class TestCreateInitHookStubsInterpreterPath:
    def test_baked_interpreter_is_an_absolute_path(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        create_init_hook_stubs(hooks_dir, force=False)

        for name in _STUB_NAMES:
            content = (hooks_dir / name).read_text(encoding="utf-8")
            assert '"{}"'.format(sys.executable) in content
        assert os.path.isabs(sys.executable)


class TestCreateInitHookStubsPreExistingDir:
    def test_unrelated_dir_contents_do_not_require_force(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        create_init_hook_stubs(hooks_dir, force=False)

        assert sample.read_text() == "git's own sample hook"
        _assert_installed(hooks_dir)


class TestCreateInitHookStubsConflict:
    def test_without_force_raises_and_leaves_stubs_untouched(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _STUB_NAMES:
            (hooks_dir / name).write_text("stale content")

        with pytest.raises(SystemExit) as exc_info:
            create_init_hook_stubs(hooks_dir, force=False)

        assert exc_info.value.code == 1
        for name in _STUB_NAMES:
            assert (hooks_dir / name).read_text() == "stale content"

    def test_with_force_overrides_stale_content(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _STUB_NAMES:
            (hooks_dir / name).write_text("stale content")

        create_init_hook_stubs(hooks_dir, force=True)

        _assert_installed(hooks_dir)
