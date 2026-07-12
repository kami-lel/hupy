"""
stub-update_stubs_verify_hook_stubs_test.py

tests for `verify_hook_stubs`: no-op sync check (warns on
missing/unused, unrelated dir contents ignored), --update adds
missing/removes unused while leaving already-installed stubs
untouched, --update --force additionally regenerates already-installed
stubs
"""

import sys

from hupy.stub.update_stubs import install_hook_stubs, verify_hook_stubs

# helpers  ######################################################################


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


class TestVerifyHookStubsSyncNoOp:
    def test_missing_and_unused_are_reported_but_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        install_hook_stubs(repo, hooks_dir=hooks_dir, force=False)
        missing_name = stub_names[0]
        (hooks_dir / missing_name).unlink()
        unused_path = _write_unmanaged_stub(hooks_dir, "unused-hook")

        verify_hook_stubs(repo, hooks_dir=hooks_dir, force=False)

        assert not (hooks_dir / missing_name).exists()
        assert unused_path.exists()
        for name in stub_names[1:]:
            assert (hooks_dir / name).exists()

    def test_unrelated_dir_contents_are_ignored(self, tmp_path, repo):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        sample = hooks_dir / "pre-commit.sample"
        sample.write_text("git's own sample hook")

        verify_hook_stubs(repo, hooks_dir=hooks_dir, force=False)

        assert sample.read_text() == "git's own sample hook"
        assert sorted(p.name for p in hooks_dir.iterdir()) == [
            "pre-commit.sample"
        ]


class TestVerifyHookStubsUpdate:
    def test_update_adds_missing_and_removes_unused(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        install_hook_stubs(repo, hooks_dir=hooks_dir, force=False)
        missing_name = stub_names[0]
        (hooks_dir / missing_name).unlink()
        _write_unmanaged_stub(hooks_dir, "unused-hook")

        verify_hook_stubs(repo, hooks_dir=hooks_dir, force=False, update=True)

        assert sorted(p.name for p in hooks_dir.iterdir()) == stub_names
        _assert_installed(hooks_dir, stub_names)

    def test_update_leaves_already_installed_stubs_untouched(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        install_hook_stubs(repo, hooks_dir=hooks_dir, force=False)
        target = hooks_dir / stub_names[0]
        target.write_text(target.read_text() + "stale marker\n")

        verify_hook_stubs(repo, hooks_dir=hooks_dir, force=False, update=True)

        assert "stale marker" in target.read_text()

    def test_update_with_force_also_replaces_installed_stubs(
        self, tmp_path, repo, stub_names
    ):
        hooks_dir = tmp_path / "hooks"
        install_hook_stubs(repo, hooks_dir=hooks_dir, force=False)
        target = hooks_dir / stub_names[0]
        target.write_text(target.read_text() + "stale marker\n")

        verify_hook_stubs(repo, hooks_dir=hooks_dir, force=True, update=True)

        assert "stale marker" not in target.read_text()
        _assert_installed(hooks_dir, stub_names)
