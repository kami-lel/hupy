"""
stub-update_stubs_update_hooks_stub_test.py

tests for `update_hooks_stub`: the `is_init` create path (fresh dir,
pre-existing but unrelated dir contents, per-file conflict abort
without --force, override with --force, baking the interpreter path
into installed stubs, only by-demand hook names get installed), and
the non-`is_init` sync path (no-op check, --update-hook-stub adds
missing/removes unused, --update-hook-stub --force also replaces
already-installed stubs)
"""

import os
import sys

import pytest

from hupy.stub.names_by_demand import get_hook_names_by_demand
from hupy.stub.update_stubs import update_hooks_stub

_STUB_NAMES = sorted(get_hook_names_by_demand())


# helpers  ######################################################################


def _assert_installed(hooks_dir):
    for name in _STUB_NAMES:
        content = (hooks_dir / name).read_text(encoding="utf-8")
        assert content.startswith("#!/usr/bin/env bash\n")
        assert sys.executable in content
        assert "-m hupy hook {}".format(name) in content


# tests  ########################################################################


class TestUpdateHooksStubFreshDir:
    def test_creates_missing_dir_and_installs_demanded_stubs(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        update_hooks_stub(hooks_dir, force=False, is_init=True)

        assert hooks_dir.is_dir()
        assert sorted(p.name for p in hooks_dir.iterdir()) == _STUB_NAMES
        _assert_installed(hooks_dir)

    def test_installed_stubs_are_executable(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        update_hooks_stub(hooks_dir, force=False, is_init=True)

        for name in _STUB_NAMES:
            assert os.access(str(hooks_dir / name), os.X_OK)


class TestUpdateHooksStubInterpreterPath:
    def test_baked_interpreter_is_an_absolute_path(self, tmp_path):
        hooks_dir = tmp_path / "hooks"

        update_hooks_stub(hooks_dir, force=False, is_init=True)

        for name in _STUB_NAMES:
            content = (hooks_dir / name).read_text(encoding="utf-8")
            assert '"{}"'.format(sys.executable) in content
        assert os.path.isabs(sys.executable)


class TestUpdateHooksStubPreExistingDir:
    def test_unrelated_dir_contents_do_not_require_force(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        update_hooks_stub(hooks_dir, force=False, is_init=True)

        assert sample.read_text() == "git's own sample hook"
        _assert_installed(hooks_dir)


class TestUpdateHooksStubConflict:
    def test_without_force_raises_and_leaves_stubs_untouched(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _STUB_NAMES:
            (hooks_dir / name).write_text("stale content")

        with pytest.raises(SystemExit) as exc_info:
            update_hooks_stub(hooks_dir, force=False, is_init=True)

        assert exc_info.value.code == 1
        for name in _STUB_NAMES:
            assert (hooks_dir / name).read_text() == "stale content"

    def test_with_force_overrides_stale_content(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in _STUB_NAMES:
            (hooks_dir / name).write_text("stale content")

        update_hooks_stub(hooks_dir, force=True, is_init=True)

        _assert_installed(hooks_dir)


class TestUpdateHooksStubSyncNoOp:
    def test_missing_and_unused_are_reported_but_untouched(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        update_hooks_stub(hooks_dir, force=False, is_init=True)
        missing_name = _STUB_NAMES[0]
        (hooks_dir / missing_name).unlink()
        unused_path = hooks_dir / "unused-hook"
        unused_path.write_text(
            '#!/usr/bin/env bash\n"{}" -m hupy hook unused-hook "$@"\n'.format(
                sys.executable
            )
        )

        update_hooks_stub(hooks_dir, force=False)

        assert not (hooks_dir / missing_name).exists()
        assert unused_path.exists()
        for name in _STUB_NAMES[1:]:
            assert (hooks_dir / name).exists()

    def test_unrelated_dir_contents_are_ignored(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        update_hooks_stub(hooks_dir, force=False)

        assert sample.read_text() == "git's own sample hook"
        assert sorted(p.name for p in hooks_dir.iterdir()) == ["pre-commit.sample"]


class TestUpdateHooksStubUpdate:
    def test_update_adds_missing_and_removes_unused(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        update_hooks_stub(hooks_dir, force=False, is_init=True)
        missing_name = _STUB_NAMES[0]
        (hooks_dir / missing_name).unlink()
        unused_path = hooks_dir / "unused-hook"
        unused_path.write_text(
            '#!/usr/bin/env bash\n"{}" -m hupy hook unused-hook "$@"\n'.format(
                sys.executable
            )
        )

        update_hooks_stub(hooks_dir, force=False, update=True)

        assert sorted(p.name for p in hooks_dir.iterdir()) == _STUB_NAMES
        _assert_installed(hooks_dir)

    def test_update_leaves_already_installed_stubs_untouched(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        update_hooks_stub(hooks_dir, force=False, is_init=True)
        target = hooks_dir / _STUB_NAMES[0]
        target.write_text(
            '#!/usr/bin/env bash\n"{}" -m hupy hook {} "$@"\nstale marker\n'.format(
                sys.executable, _STUB_NAMES[0]
            )
        )

        update_hooks_stub(hooks_dir, force=False, update=True)

        assert "stale marker" in target.read_text()

    def test_update_with_force_also_replaces_installed_stubs(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        update_hooks_stub(hooks_dir, force=False, is_init=True)
        target = hooks_dir / _STUB_NAMES[0]
        target.write_text(
            '#!/usr/bin/env bash\n"{}" -m hupy hook {} "$@"\nstale marker\n'.format(
                sys.executable, _STUB_NAMES[0]
            )
        )

        update_hooks_stub(hooks_dir, force=True, update=True)

        assert "stale marker" not in target.read_text()
        _assert_installed(hooks_dir)
