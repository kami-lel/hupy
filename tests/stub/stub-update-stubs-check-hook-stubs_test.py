"""
stub-update-stubs-check-hook-stubs_test.py

tests for `check_hook_stubs`: classifies missing, stale, and unused
hook names purely by reading, ignores unrelated dir contents, never
writes anything, and reports every demanded name as missing when the
hooks dir itself is absent
"""

import sys

from hupy.stub.update_stubs import check_hook_stubs, sync_hook_stubs

# auxiliaries  #################################################################


def _write_unmanaged_stub(hooks_dir, hook_name):
    stub_path = hooks_dir / hook_name
    stub_path.write_text(
        '#!/usr/bin/env bash\n"{}" -m hupy hook {} "$@"\n'.format(
            sys.executable, hook_name
        )
    )
    return stub_path


# tests  ########################################################################


class TestCheckHookStubsClean:
    def test_freshly_synced_dir_reports_nothing(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)

        missing_names, stale_names, unused_names = check_hook_stubs(
            repo, hooks_dir=hooks_dir
        )

        assert missing_names == []
        assert stale_names == []
        assert unused_names == []


class TestCheckHookStubsMissing:
    def test_absent_hooks_dir_reports_every_demanded_name_as_missing(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"

        missing_names, stale_names, unused_names = check_hook_stubs(
            repo, hooks_dir=hooks_dir
        )

        assert missing_names == stub_names
        assert stale_names == []
        assert unused_names == []
        assert not hooks_dir.exists()

    def test_removed_stub_is_reported_missing(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        missing_name = stub_names[0]
        (hooks_dir / missing_name).unlink()

        missing_names, _, _ = check_hook_stubs(repo, hooks_dir=hooks_dir)

        assert missing_names == [missing_name]


class TestCheckHookStubsStale:
    def test_hand_edited_stub_is_reported_stale(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        stale_name = stub_names[0]
        target = hooks_dir / stale_name
        target.write_text(target.read_text() + "stale marker\n")

        _, stale_names, _ = check_hook_stubs(repo, hooks_dir=hooks_dir)

        assert stale_names == [stale_name]


class TestCheckHookStubsUnused:
    def test_no_longer_demanded_stub_is_reported_unused(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        _write_unmanaged_stub(hooks_dir, "unused-hook")

        _, _, unused_names = check_hook_stubs(repo, hooks_dir=hooks_dir)

        assert unused_names == ["unused-hook"]

    def test_unrelated_dir_contents_are_ignored(self, tmp_path, repo):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        missing_names, stale_names, unused_names = check_hook_stubs(
            repo, hooks_dir=hooks_dir
        )

        assert unused_names == []
        assert sample.read_text() == "git's own sample hook"


class TestCheckHookStubsReadOnly:
    def test_check_writes_nothing_to_an_absent_hooks_dir(
        self, tmp_path, repo
    ):
        hooks_dir = tmp_path / "hooks"

        check_hook_stubs(repo, hooks_dir=hooks_dir)

        assert not hooks_dir.exists()

    def test_check_leaves_an_existing_hooks_dir_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        sync_hook_stubs(repo, hooks_dir=hooks_dir)
        before = sorted(p.name for p in hooks_dir.iterdir())

        check_hook_stubs(repo, hooks_dir=hooks_dir)

        after = sorted(p.name for p in hooks_dir.iterdir())
        assert before == after
