"""
setup-parser_init_cli_test.py

end-to-end tests for the `init` CLI subcommand: default hooks dir,
`--hooks-dir` override, `-f`/`--force` re-runs, subdirectory
resolution, and error paths for non-git or nonexistent targets
"""

import pytest

from setup_helpers import read_hooks_path, run_init_cli

_TEMPLATE_NAMES = ("pre-commit.bash", "prepare-commit-msg.bash")


# tests  ########################################################################


class TestInitDefaultHooksDir:
    def test_copies_scripts_and_sets_hooks_path(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        hooks_dir = git_repo_dir / "scripts" / "hupy-hooks"
        assert hooks_dir.is_dir()
        for name in _TEMPLATE_NAMES:
            assert (hooks_dir / name).exists()
        assert read_hooks_path(git_repo_dir) == str(hooks_dir)

    def test_resolves_from_subdirectory_to_repo_root(self, git_repo_dir):
        sub_dir = git_repo_dir / "sub" / "dir"
        sub_dir.mkdir(parents=True)

        run_init_cli([str(sub_dir)])

        hooks_dir = git_repo_dir / "scripts" / "hupy-hooks"
        assert hooks_dir.is_dir()
        assert not (sub_dir / "scripts").exists()
        assert read_hooks_path(git_repo_dir) == str(hooks_dir)


class TestInitCustomHooksDir:
    def test_hooks_dir_flag_overrides_default(self, git_repo_dir):
        custom_dir = git_repo_dir / "custom-hooks"

        run_init_cli([str(git_repo_dir), "--hooks-dir", str(custom_dir)])

        assert custom_dir.is_dir()
        for name in _TEMPLATE_NAMES:
            assert (custom_dir / name).exists()
        assert not (git_repo_dir / "scripts" / "hupy-hooks").exists()
        assert read_hooks_path(git_repo_dir) == str(custom_dir)


class TestInitForceReRun:
    def test_rerun_without_force_raises_system_exit(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(git_repo_dir)])

        assert exc_info.value.code == 1

    def test_rerun_with_force_overrides_stale_scripts(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = git_repo_dir / "scripts" / "hupy-hooks"
        (hooks_dir / "pre-commit.bash").write_text("stale content")

        run_init_cli([str(git_repo_dir), "-f"])

        assert (hooks_dir / "pre-commit.bash").read_text() != "stale content"


class TestInitErrors:
    def test_not_a_git_repository_raises_system_exit(self, tmp_path):
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(not_a_repo)])

        assert exc_info.value.code == 1
        assert not (not_a_repo / "scripts").exists()

    def test_nonexistent_path_raises_system_exit(self, tmp_path):
        missing = tmp_path / "does-not-exist"

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(missing)])

        assert exc_info.value.code == 1


class TestInitVerbosity:
    def test_verbose_flag_does_not_break_init(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "-v"])

        assert (git_repo_dir / "scripts" / "hupy-hooks").is_dir()

    def test_quiet_flag_does_not_break_init(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "-q"])

        assert (git_repo_dir / "scripts" / "hupy-hooks").is_dir()
