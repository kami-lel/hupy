"""
cli-verify_test.py

end-to-end tests for the `verify` CLI subcommand: exits 0 with hook
stub drift present (missing/stale/unused only warn), exits 1 on a
missing or malformed config file, never writes `hupy-state.json`, and
error paths for non-git targets
"""

import json

import git
import json5
import pytest

from hupy.config_file.config_file_path import CONFIG_FILENAME
from hupy.state.state_file_path import STATE_FILENAME
from . import run_init_cli, run_verify_cli

# tests  ########################################################################


class TestVerifyCleanRepo:
    def test_freshly_initialized_repo_verifies_clean(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        run_verify_cli([str(git_repo_dir)])


class TestVerifyHookStubDrift:
    def test_missing_stub_does_not_raise(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = git_repo_dir / ".git" / "hooks"
        (hooks_dir / stub_names[0]).unlink()

        run_verify_cli([str(git_repo_dir)])

    def test_missing_stub_is_left_missing(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = git_repo_dir / ".git" / "hooks"
        target = hooks_dir / stub_names[0]
        target.unlink()

        run_verify_cli([str(git_repo_dir)])

        assert not target.exists()

    def test_stale_stub_is_left_untouched(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = git_repo_dir / ".git" / "hooks"
        target = hooks_dir / stub_names[0]
        target.write_text(target.read_text() + "stale marker\n")

        run_verify_cli([str(git_repo_dir)])

        assert "stale marker" in target.read_text()

    def test_unused_stub_is_left_in_place(self, git_repo_dir, stub_names):
        run_init_cli([str(git_repo_dir)])
        hooks_dir = git_repo_dir / ".git" / "hooks"
        unused_path = hooks_dir / "unused-hook"
        unused_path.write_text("#!/usr/bin/env bash\necho unused\n")

        run_verify_cli([str(git_repo_dir)])

        assert unused_path.exists()


class TestVerifyConfigFile:
    def test_missing_config_file_raises_system_exit(self, git_repo_dir):
        run_init_cli([str(git_repo_dir), "--only", "stubs"])

        with pytest.raises(SystemExit) as exc_info:
            run_verify_cli([str(git_repo_dir)])

        assert exc_info.value.code == 1

    def test_malformed_config_file_raises_system_exit(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])
        (git_repo_dir / CONFIG_FILENAME).write_text("not valid json5 {{{")

        with pytest.raises(SystemExit) as exc_info:
            run_verify_cli([str(git_repo_dir)])

        assert exc_info.value.code == 1


class TestVerifyVersionUniformity:
    def test_drifted_occurrence_does_not_change_exit_code(
        self, git_repo_dir
    ):
        run_init_cli([str(git_repo_dir)])

        repo = git.Repo(str(git_repo_dir))
        (git_repo_dir / "VERSION").write_text("1.0.0\n")
        (git_repo_dir / "OTHER").write_text("2.0.0\n")
        repo.index.add(["VERSION", "OTHER"])
        repo.index.commit("add version files")

        config_path = git_repo_dir / CONFIG_FILENAME
        config = json5.loads(config_path.read_text())
        config["vg"]["version_occurrences"] = [
            {"file": "VERSION", "glob": r"(\d+\.\d+\.\d+)"},
            {"file": "OTHER", "glob": r"(\d+\.\d+\.\d+)"},
        ]
        config_path.write_text(json.dumps(config))

        run_verify_cli([str(git_repo_dir)])


class TestVerifyDoesNotWriteState:
    def test_no_state_file_is_created(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        run_verify_cli([str(git_repo_dir)])

        assert not (git_repo_dir / ".git" / STATE_FILENAME).exists()


class TestVerifyErrors:
    def test_not_a_git_repository_raises_system_exit(self, tmp_path):
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            run_verify_cli([str(not_a_repo)])

        assert exc_info.value.code == 1


class TestVerifyVerbosity:
    def test_verbose_flag_does_not_break_verify(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        run_verify_cli([str(git_repo_dir), "-v"])

    def test_quiet_flag_does_not_break_verify(self, git_repo_dir):
        run_init_cli([str(git_repo_dir)])

        run_verify_cli([str(git_repo_dir), "-q"])
