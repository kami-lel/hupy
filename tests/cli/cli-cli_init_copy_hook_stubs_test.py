"""
cli-cli_init_copy_hook_stubs_test.py

tests for `_copy_hook_stubs`: fresh dir, pre-existing (but unrelated)
dir contents, per-file conflict abort without --force, and override
with --force
"""

import os

import pytest

from hupy.cli.cli_init import _HOOK_STUBS_DIR, _copy_hook_stubs

_STUB_NAMES = sorted(p.name for p in _HOOK_STUBS_DIR.iterdir())


# helpers  ######################################################################


def _assert_matches_templates(hooks_dir):
    for stub_file in _HOOK_STUBS_DIR.iterdir():
        copied = hooks_dir / stub_file.name
        assert copied.read_bytes() == stub_file.read_bytes()


# tests  ########################################################################


class TestCopyHookStubsFreshDir:
    def test_creates_missing_dir_and_copies_all_stubs(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        _copy_hook_stubs(hooks_dir, force=False)

        assert hooks_dir.is_dir()
        _assert_matches_templates(hooks_dir)

    def test_copied_stubs_are_executable(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        _copy_hook_stubs(hooks_dir, force=False)

        for name in _STUB_NAMES:
            assert os.access(str(hooks_dir / name), os.X_OK)


class TestCopyHookStubsPreExistingDir:
    def test_unrelated_dir_contents_do_not_require_force(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        _copy_hook_stubs(hooks_dir, force=False)

        assert sample.read_text() == "git's own sample hook"
        _assert_matches_templates(hooks_dir)


class TestCopyHookStubsConflict:
    def test_without_force_raises_and_leaves_stubs_untouched(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _STUB_NAMES:
            (hooks_dir / name).write_text("stale content")

        with pytest.raises(SystemExit) as exc_info:
            _copy_hook_stubs(hooks_dir, force=False)

        assert exc_info.value.code == 1
        for name in _STUB_NAMES:
            assert (hooks_dir / name).read_text() == "stale content"

    def test_with_force_overrides_stale_content(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _STUB_NAMES:
            (hooks_dir / name).write_text("stale content")

        _copy_hook_stubs(hooks_dir, force=True)

        _assert_matches_templates(hooks_dir)
