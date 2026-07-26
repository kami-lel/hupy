"""
cli-init_test.py

end-to-end tests for the `init` CLI subcommand: default (.git/hooks)
target, honoring a pre-configured `core.hooksPath`, `--hooks-dir`
override, `--only` step selection, convergent repeat runs,
`-f`/`--force` and `--prune`, subdirectory resolution, config-file
writing, and error paths for non-git or nonexistent targets
"""

import pytest

from hupy.config_file.config_file_path import (
    CONFIG_FILENAME,
    DEFAULT_CONFIG_ASSET,
)
from . import get_configured_hooks_path, run_init_cli, set_configured_hooks_path

_DEFAULT_CONFIG_CONTENT = DEFAULT_CONFIG_ASSET.read_text()

# a schema-valid but stale config: hook-demand checks now parse the
# config file, so a pre-existing config must stay parseable even when
# standing in for stale/outdated content
_STALE_VALID_CONFIG_CONTENT = _DEFAULT_CONFIG_CONTENT.replace(
    '"hupy_version": "1.0.0"', '"hupy_version": "0.0.1"'
)


# auxiliaries  #################################################################


def _default_hooks_dir(git_repo_dir):
    return git_repo_dir / ".git" / "hooks"


# tests  ########################################################################


class TestInitDefaultHooksDir:
    def test_copies_stubs_into_dot_git_hooks(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir)])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in stub_names:
            assert (hooks_dir / name).exists()

    def test_does_not_set_core_hooks_path(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        assert get_configured_hooks_path(git_repo_dir) is None

    def test_resolves_from_subdirectory_to_repo_root(
        self, git_repo_dir, stub_names
    ):
        sub_dir = git_repo_dir / "sub" / "dir"
        sub_dir.mkdir(parents=True)

        run_init_cli([str(sub_dir)])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in stub_names:
            assert (hooks_dir / name).exists()
        assert not (sub_dir / ".git").exists()


class TestInitHonorsConfiguredHooksPath:
    def test_copies_stubs_to_preconfigured_hooks_path(
        self, git_repo_dir, stub_names
    ):
        custom_dir = git_repo_dir / "custom-hooks"
        set_configured_hooks_path(git_repo_dir, "custom-hooks")

        run_init_cli([str(git_repo_dir)])

        for name in stub_names:
            assert (custom_dir / name).exists()
        for name in stub_names:
            assert not (_default_hooks_dir(git_repo_dir) / name).exists()


class TestInitCustomHooksDirFlag:
    def test_hooks_dir_flag_overrides_default(self, git_repo_dir, stub_names):
        custom_dir = git_repo_dir / "flag-hooks"

        run_init_cli([str(git_repo_dir), "--hooks-dir", str(custom_dir)])

        for name in stub_names:
            assert (custom_dir / name).exists()
        for name in stub_names:
            assert not (_default_hooks_dir(git_repo_dir) / name).exists()

    def test_hooks_dir_flag_overrides_configured_hooks_path(
        self, git_repo_dir, stub_names
    ):
        set_configured_hooks_path(git_repo_dir, "configured-hooks")
        custom_dir = git_repo_dir / "flag-hooks"

        run_init_cli([str(git_repo_dir), "--hooks-dir", str(custom_dir)])

        for name in stub_names:
            assert (custom_dir / name).exists()
        for name in stub_names:
            assert not ((git_repo_dir / "configured-hooks") / name).exists()


class TestInitWritesConfigFile:
    def test_writes_config_matching_model_defaults(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT


class TestInitOnlyFlag:
    def test_only_stubs_skips_config_file(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir), "--only", "stubs"])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in stub_names:
            assert (hooks_dir / name).exists()
        assert not (git_repo_dir / CONFIG_FILENAME).exists()

    def test_only_config_skips_hooks(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir), "--only", "config"])

        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in stub_names:
            assert not (hooks_dir / name).exists()

    def test_invalid_only_value_raises_system_exit(self, git_repo_dir):
        with pytest.raises(SystemExit) as exc_info:
            run_init_cli([str(git_repo_dir), "--only", "nonsense"])

        assert exc_info.value.code == 2

    def test_no_flags_create_both_hooks_and_config(
        self, git_repo_dir, stub_names
    ):
        run_init_cli([str(git_repo_dir)])

        hooks_dir = _default_hooks_dir(git_repo_dir)
        for name in stub_names:
            assert (hooks_dir / name).exists()
        config_path = git_repo_dir / CONFIG_FILENAME
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT


class TestInitConvergentRepeatRun:
    def test_repeat_run_without_force_leaves_correct_files_untouched(
        self, git_repo_dir, stub_names
    ):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = _default_hooks_dir(git_repo_dir)
        config_path = git_repo_dir / CONFIG_FILENAME
        before_hooks_mtime = (hooks_dir / stub_names[0]).stat().st_mtime_ns
        before_config_mtime = config_path.stat().st_mtime_ns

        run_init_cli([str(git_repo_dir)])

        assert (hooks_dir / stub_names[0]).stat().st_mtime_ns == (
            before_hooks_mtime
        )
        assert config_path.stat().st_mtime_ns == before_config_mtime

    def test_repeat_run_without_force_reports_but_keeps_stale_content(
        self, git_repo_dir, stub_names
    ):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = _default_hooks_dir(git_repo_dir)
        (hooks_dir / stub_names[0]).write_text("stale content")
        config_path = git_repo_dir / CONFIG_FILENAME
        config_path.write_text(_STALE_VALID_CONFIG_CONTENT)

        run_init_cli([str(git_repo_dir)])

        assert (hooks_dir / stub_names[0]).read_text() == "stale content"
        assert config_path.read_text() == _STALE_VALID_CONFIG_CONTENT

    def test_rerun_with_force_overrides_stale_hooks_and_config(
        self, git_repo_dir, stub_names
    ):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = _default_hooks_dir(git_repo_dir)
        (hooks_dir / stub_names[0]).write_text("stale content")
        config_path = git_repo_dir / CONFIG_FILENAME
        config_path.write_text(_STALE_VALID_CONFIG_CONTENT)

        run_init_cli([str(git_repo_dir), "-f"])

        assert (hooks_dir / stub_names[0]).read_text() != "stale content"
        assert config_path.read_text() == _DEFAULT_CONFIG_CONTENT


class TestInitPruneFlag:
    def test_unused_stub_survives_without_prune(
        self, git_repo_dir, stub_names
    ):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = _default_hooks_dir(git_repo_dir)
        unused_path = hooks_dir / "unused-hook"
        unused_path.write_text(
            '#!/usr/bin/env bash\nexec "python" -m hupy hook unused-hook '
            '"$@"\n'
        )

        run_init_cli([str(git_repo_dir)])

        assert unused_path.exists()

    def test_unused_stub_is_removed_with_prune(
        self, git_repo_dir, stub_names
    ):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = _default_hooks_dir(git_repo_dir)
        unused_path = hooks_dir / "unused-hook"
        unused_path.write_text(
            '#!/usr/bin/env bash\nexec "python" -m hupy hook unused-hook '
            '"$@"\n'
        )

        run_init_cli([str(git_repo_dir), "--prune"])

        assert not unused_path.exists()


class TestInitDryRunFlag:
    def test_dry_run_writes_no_stubs(self, git_repo_dir, stub_names):
        custom_dir = git_repo_dir / "flag-hooks"

        run_init_cli(
            [str(git_repo_dir), "--hooks-dir", str(custom_dir), "-n"]
        )

        assert not custom_dir.exists()

    def test_dry_run_writes_no_config_file(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "--only", "config", "-n"])

        assert not (git_repo_dir / CONFIG_FILENAME).exists()


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
    def test_verbose_flag_does_not_break_init(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir), "-v"])

        for name in stub_names:
            assert (_default_hooks_dir(git_repo_dir) / name).exists()

    def test_quiet_flag_does_not_break_init(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir), "-q"])

        for name in stub_names:
            assert (_default_hooks_dir(git_repo_dir) / name).exists()
