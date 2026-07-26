"""
stub-update-stubs-sync-hook-stubs_test.py

tests for `sync_hook_stubs`: fresh dir, pre-existing but unrelated
dir contents, baking the interpreter path into installed stubs, a
repeat run is a silent no-op, a stale stub is left in place unless
--force, an unused stub is left in place unless --prune, and
--dry-run reports without touching the file system
"""

import os
import sys

from hupy.stub.update_stubs import sync_hook_stubs

# auxiliaries  #################################################################


def _assert_installed(hooks_dir, stub_names):
    for name in stub_names:
        content = (hooks_dir / name).read_text(encoding="utf-8")
        assert content.startswith("#!/usr/bin/env bash\n")
        assert sys.executable in content
        assert "-m hupy hook {}".format(name) in content


def _write_unmanaged_stub(hooks_dir, hook_name):
    stub_path = hooks_dir / hook_name
    stub_path.write_text(
        '#!/usr/bin/env bash\n"{}" -m hupy hook {} "$@"\n'.format(
            sys.executable, hook_name
        )
    )
    return stub_path


# tests  ########################################################################


class TestSyncHookStubsFreshDir:
    def test_creates_missing_dir_and_installs_demanded_stubs(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"

        sync_hook_stubs(repo, hooks_dir=hooks_dir)

        assert hooks_dir.is_dir()
        assert sorted(p.name for p in hooks_dir.iterdir()) == stub_names
        _assert_installed(hooks_dir, stub_names)

    def test_installed_stubs_are_executable(self, tmp_path, repo, stub_names):
        hooks_dir = tmp_path / "hooks"

        sync_hook_stubs(repo, hooks_dir=hooks_dir)

        for name in stub_names:
            assert os.access(str(hooks_dir / name), os.X_OK)


class TestSyncHookStubsInterpreterPath:
    def test_baked_interpreter_is_an_absolute_path(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"

        sync_hook_stubs(repo, hooks_dir=hooks_dir)

        for name in stub_names:
            content = (hooks_dir / name).read_text(encoding="utf-8")
            assert '"{}"'.format(sys.executable) in content
        assert os.path.isabs(sys.executable)


class TestSyncHookStubsPreExistingDir:
    def test_unrelated_dir_contents_are_left_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        sync_hook_stubs(repo, hooks_dir=hooks_dir)

        assert sample.read_text() == "git's own sample hook"
        _assert_installed(hooks_dir, stub_names)


class TestSyncHookStubsRepeatRun:
    def test_repeat_run_leaves_installed_stubs_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        before = {
            name: (hooks_dir / name).stat().st_mtime_ns for name in stub_names
        }

        sync_hook_stubs(repo, hooks_dir=hooks_dir)

        after = {
            name: (hooks_dir / name).stat().st_mtime_ns for name in stub_names
        }
        assert before == after
        _assert_installed(hooks_dir, stub_names)


class TestSyncHookStubsStale:
    def test_stale_stub_without_force_is_left_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        target = hooks_dir / stub_names[0]
        target.write_text(target.read_text() + "stale marker\n")

        sync_hook_stubs(repo, hooks_dir=hooks_dir, force=False)

        assert "stale marker" in target.read_text()

    def test_stale_stub_with_force_is_rewritten(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        target = hooks_dir / stub_names[0]
        target.write_text(target.read_text() + "stale marker\n")

        sync_hook_stubs(repo, hooks_dir=hooks_dir, force=True)

        assert "stale marker" not in target.read_text()
        _assert_installed(hooks_dir, stub_names)


class TestSyncHookStubsUnused:
    def test_unused_stub_without_prune_is_left_in_place(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        unused_path = _write_unmanaged_stub(hooks_dir, "unused-hook")

        sync_hook_stubs(repo, hooks_dir=hooks_dir, prune=False)

        assert unused_path.exists()

    def test_unused_stub_with_prune_is_removed(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        unused_path = _write_unmanaged_stub(hooks_dir, "unused-hook")

        sync_hook_stubs(repo, hooks_dir=hooks_dir, prune=True)

        assert not unused_path.exists()
        assert sorted(p.name for p in hooks_dir.iterdir()) == stub_names


class TestSyncHookStubsDryRun:
    def test_dry_run_creates_no_hooks_dir(self, tmp_path, repo):
        hooks_dir = tmp_path / "hooks"

        sync_hook_stubs(repo, hooks_dir=hooks_dir, dry_run=True)

        assert not hooks_dir.exists()

    def test_dry_run_leaves_existing_stubs_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        target = hooks_dir / stub_names[0]
        target.write_text(target.read_text() + "stale marker\n")
        unused_path = _write_unmanaged_stub(hooks_dir, "unused-hook")

        sync_hook_stubs(
            repo, hooks_dir=hooks_dir, force=True, prune=True, dry_run=True
        )

        assert "stale marker" in target.read_text()
        assert unused_path.exists()
