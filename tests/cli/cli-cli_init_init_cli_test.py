"""
cli-cli_init_init_cli_test.py

end-to-end tests for the `init` CLI subcommand: default (.git/hooks)
target, honoring a pre-configured `core.hooksPath`, `--hooks-dir`
override, `-f`/`--force` re-runs, subdirectory resolution, config-file
writing, and error paths for non-git or nonexistent targets
"""

import pytest

from hupy.config.load_config import CONFIG_FILENAME
from hupy.config.write_config import DEFAULT_CONFIG_ASSET
from hupy.cli.cli_init import _HOOK_STUBS_DIR
from cli_helpers import (
    get_configured_hooks_path,
    run_init_cli,
    set_configured_hooks_path,
)

_STUB_NAMES = sorted(p.name for p in _HOOK_STUBS_DIR.iterdir())
_DEFAULT_CONFIG_CONTENT = DEFAULT_CONFIG_ASSET.read_text()


# helpers  ######################################################################


def _default_hooks_dir(git_repo_dir):
    return git_repo_dir / ".git" / "hooks"


# tests  ########################################################################


class TestInitDefaultHooksDir:
    def test_copies_stubs_into_dot_git_hooks(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert (hooks_dir / name).exists()

    def test_does_not_set_core_hooks_path(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        assert get_configured_hooks_path(git_repo_dir) is None

    def test_resolves_from_subdirectory_to_repo_root(self, git_repo_dir):
        sub_dir = git_repo_dir / "sub" / "dir"
        sub_dir.mkdir(parents=True)

        run_init_cli([str(sub_dir)])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert (hooks_dir / name).exists()
        assert not (sub_dir / ".git").exists()


class TestInitHonorsConfiguredHooksPath:
    def test_copies_stubs_to_preconfigured_hooks_path(self, git_repo_dir):
        custom_dir = git_repo_dir / "custom-hooks"
        set_configured_hooks_path(git_repo_dir, "custom-hooks")

        run_init_cli([str(git_repo_dir)])

        for name in _STUB_NAMES:
            assert (custom_dir / name).exists()
        for name in _STUB_NAMES:
            assert not (_default_hooks_dir(git_repo_dir) / name).exists()


class TestInitCustomHooksDirFlag:
    def test_hooks_dir_flag_overrides_default(self, git_repo_dir):
        custom_dir = git_repo_dir / "flag-hooks"

        run_init_cli([str(git_repo_dir), "--hooks-dir", str(custom_dir)])

        for name in _STUB_NAMES:
            assert (custom_dir / name).exists()
        for name in _STUB_NAMES:
            assert not (_default_hooks_dir(git_repo_dir) / name).exists()

    def test_hooks_dir_flag_overrides_configured_hooks_path(self, git_repo_dir):
        set_configured_hooks_path(git_repo_dir, "configured-hooks")
        custom_dir = git_repo_dir / "flag-hooks"

        run_init_cli([str(git_repo_dir), "--hooks-dir", str(custom_dir)])

        for name in _STUB_NAMES:
            assert (custom_dir / name).exists()
        for name in _STUB_NAMES:
            assert not (
                (git_repo_dir / "configured-hooks") / name
            ).exists()


class TestInitWritesConfigFile:
    def test_writes_config_matching_model_defaults(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT


class TestInitStepFlags:
    def test_copy_hooks_flag_skips_config_file(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "--copy-hooks"])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert (hooks_dir / name).exists()
        assert not (git_repo_dir / CONFIG_FILENAME).exists()

    def test_create_config_file_flag_skips_hooks(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "--create-config-file"])

        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert not (hooks_dir / name).exists()

    def test_both_flags_together_create_hooks_and_config(self, git_repo_dir):
        run_init_cli(
            [str(git_repo_dir), "--copy-hooks", "--create-config-file"]
        )

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert (hooks_dir / name).exists()
        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT

    def test_no_flags_create_both_hooks_and_config(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert (hooks_dir / name).exists()
        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT


class TestInitForceReRun:
    def test_rerun_without_force_raises_system_exit(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(git_repo_dir)])

        assert exc_info.value.code == 1

    def test_rerun_with_force_overrides_stale_hooks_and_config(
        self, git_repo_dir
    ):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = _default_hooks_dir(git_repo_dir)
        (hooks_dir / _STUB_NAMES[0]).write_text("stale content")
        config_path = git_repo_dir / CONFIG_FILENAME
        config_path.write_text("stale content")

        run_init_cli([str(git_repo_dir), "-f"])

        assert (hooks_dir / _STUB_NAMES[0]).read_text() != "stale content"
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT

    def test_config_conflict_alone_still_raises_after_hooks_succeed(
        self, git_repo_dir
    ):
        (git_repo_dir / CONFIG_FILENAME).write_text("stale content")

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(git_repo_dir)])

        assert exc_info.value.code == 1
        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in _STUB_NAMES:
            assert (hooks_dir / name).exists()
        assert (git_repo_dir / CONFIG_FILENAME).read_text() == "stale content"


class TestInitErrors:
    def test_not_a_git_repository_raises_system_exit(self, tmp_path):
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(not_a_repo)])

        assert exc_info.value.code == 1
        assert not (not_a_repo / CONFIG_FILENAME).exists()

    def test_nonexistent_path_raises_system_exit(self, tmp_path):
        missing = tmp_path / "does-not-exist"

        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(missing)])

        assert exc_info.value.code == 1


class TestInitVerbosity:
    def test_verbose_flag_does_not_break_init(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "-v"])

        for name in _STUB_NAMES:
            assert (_default_hooks_dir(git_repo_dir) / name).exists()

    def test_quiet_flag_does_not_break_init(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "-q"])

        for name in _STUB_NAMES:
            assert (_default_hooks_dir(git_repo_dir) / name).exists()
