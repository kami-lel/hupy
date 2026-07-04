"""
setup-parser_copy_hooks_scripts_test.py

tests for `_copy_hooks_scripts`: fresh copy, existing-dir abort
without --force, and override with --force
"""

import os

import pytest

from hupy.setup.parser import _HOOKS_TEMPLATES_DIR, _copy_hooks_scripts

_TEMPLATE_NAMES = sorted(p.name for p in _HOOKS_TEMPLATES_DIR.iterdir())


# helpers  ######################################################################


def _assert_matches_templates(hooks_dir):
    copied_names = sorted(p.name for p in hooks_dir.iterdir())
    assert copied_names == _TEMPLATE_NAMES
    for template_file in _HOOKS_TEMPLATES_DIR.iterdir():
        copied = hooks_dir / template_file.name
        assert copied.read_bytes() == template_file.read_bytes()


# tests  ########################################################################


class TestCopyHooksScriptsFreshDir:
    def test_creates_dir_and_copies_all_templates(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        _copy_hooks_scripts(hooks_dir, force=False)

        assert hooks_dir.is_dir()
        _assert_matches_templates(hooks_dir)

    def test_copied_scripts_are_executable(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        _copy_hooks_scripts(hooks_dir, force=False)

        for copied in hooks_dir.iterdir():
            assert os.access(str(copied), os.X_OK)


class TestCopyHooksScriptsExistingDir:
    def test_without_force_raises_and_leaves_dir_untouched(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sentinel = hooks_dir / "keep-me.txt"
        sentinel.write_text("do not touch")

        with pytest.raises(SystemExit) as exc_info:
            _copy_hooks_scripts(hooks_dir, force=False)

        assert exc_info.value.code == 1
        assert sentinel.read_text() == "do not touch"
        for name in _TEMPLATE_NAMES:
            assert not (hooks_dir / name).exists()

    def test_with_force_overrides_stale_content(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _TEMPLATE_NAMES:
            (hooks_dir / name).write_text("stale content")

        _copy_hooks_scripts(hooks_dir, force=True)

        _assert_matches_templates(hooks_dir)
