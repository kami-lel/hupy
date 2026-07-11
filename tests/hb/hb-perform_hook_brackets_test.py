"""
hb-perform_hook_brackets_test.py

tests for `perform_hook_brackets` in `perform_hook_brackets.py`
"""

from types import SimpleNamespace
from unittest import mock

import pytest

from config_fixture import load_config_fixture

from hupy.cbm import CommitType
from hupy.hb import perform_hook_brackets
from hupy.state.state_file import HupyStateFile

_REPO = SimpleNamespace(working_tree_dir="/repo")


# helpers  ######################################################################


def _result(returncode):
    return SimpleNamespace(returncode=returncode)


def _run(
    hook_name,
    is_lead,
    pre_commit_lead=(),
    pre_commit_trail=(),
    prepare_commit_msg_lead=(),
    prepare_commit_msg_trail=(),
    is_disabled=False,
    skip_once=(),
    commit_type=CommitType.REGULAR_COMMIT,
    run_returncodes=(),
):
    """
    run ``perform_hook_brackets`` against a stubbed config, commit
    type, and ``subprocess.run``, bypassing disk/git config loading
    and real command execution.


    :return: the call's result (``None`` unless it raises), the
            recorded ``subprocess.run`` calls, and the state file
            afterward
    :rtype: tuple[object, list[unittest.mock.call], HupyStateFile]
    """
    config = load_config_fixture(
        overrides={
            "hb": {
                "is_disabled": is_disabled,
                "pre_commit": {
                    "lead": list(pre_commit_lead),
                    "trail": list(pre_commit_trail),
                },
                "prepare_commit_msg": {
                    "lead": list(prepare_commit_msg_lead),
                    "trail": list(prepare_commit_msg_trail),
                },
            }
        }
    )
    state_file = HupyStateFile(skip_once=set(skip_once))

    with mock.patch(
        "hupy.hb.perform_hook_brackets.load_hupy_config", return_value=config
    ), mock.patch(
        "hupy.should_run_module.load_hupy_config", return_value=config
    ), mock.patch(
        "hupy.hb.perform_hook_brackets.get_current_commit_type",
        return_value=commit_type,
    ), mock.patch(
        "hupy.hb.perform_hook_brackets.subprocess.run",
        side_effect=[_result(rc) for rc in run_returncodes],
    ) as run_mock:
        result = perform_hook_brackets(_REPO, state_file, hook_name, is_lead)

    return result, run_mock.call_args_list, state_file


# tests  ########################################################################


class TestPerformHookBracketsFourUsageCases:
    def test_pre_commit_lead_runs_configured_commands(self):
        _, calls, _ = _run(
            "pre-commit",
            True,
            pre_commit_lead=[{"cmd": "echo lead"}],
            run_returncodes=[0],
        )
        assert calls == [
            mock.call("echo lead", shell=True, cwd="/repo"),
        ]

    def test_pre_commit_trail_runs_configured_commands(self):
        _, calls, _ = _run(
            "pre-commit",
            False,
            pre_commit_trail=[{"cmd": "echo trail"}],
            run_returncodes=[0],
        )
        assert calls == [
            mock.call("echo trail", shell=True, cwd="/repo"),
        ]

    def test_prepare_commit_msg_lead_runs_configured_commands(self):
        _, calls, _ = _run(
            "prepare-commit-msg",
            True,
            prepare_commit_msg_lead=[{"cmd": "echo pcm-lead"}],
            run_returncodes=[0],
        )
        assert calls == [
            mock.call("echo pcm-lead", shell=True, cwd="/repo"),
        ]

    def test_prepare_commit_msg_trail_runs_configured_commands(self):
        _, calls, _ = _run(
            "prepare-commit-msg",
            False,
            prepare_commit_msg_trail=[{"cmd": "echo pcm-trail"}],
            run_returncodes=[0],
        )
        assert calls == [
            mock.call("echo pcm-trail", shell=True, cwd="/repo"),
        ]


class TestPerformHookBracketsSkips:
    def test_hb_disabled_skips_before_reading_bracket(self):
        _, calls, _ = _run(
            "pre-commit",
            True,
            pre_commit_lead=[{"cmd": "echo lead"}],
            is_disabled=True,
        )
        assert calls == []

    def test_skip_once_flag_skips_and_is_consumed(self):
        _, calls, state_file = _run(
            "pre-commit",
            True,
            pre_commit_lead=[{"cmd": "echo lead"}],
            skip_once={"hb"},
        )
        assert calls == []
        assert "hb" not in state_file.skip_once

    def test_empty_commands_list_runs_nothing(self):
        result, calls, _ = _run("pre-commit", True)
        assert result is None
        assert calls == []


class TestPerformHookBracketsUnrecognizedHook:
    def test_unknown_hook_name_raises_value_error(self):
        with pytest.raises(ValueError):
            _run("unknown-hook", True)


class TestPerformHookBracketsCommitTypeFilter:
    def test_matching_commit_type_runs_command(self):
        _, calls, _ = _run(
            "pre-commit",
            True,
            pre_commit_lead=[
                {"cmd": "echo lead", "commit_types": ["FEATURE_LANDING"]}
            ],
            commit_type=CommitType.FEATURE_LANDING,
            run_returncodes=[0],
        )
        assert calls == [mock.call("echo lead", shell=True, cwd="/repo")]

    def test_mismatched_commit_type_skips_command(self):
        _, calls, _ = _run(
            "pre-commit",
            True,
            pre_commit_lead=[
                {"cmd": "echo lead", "commit_types": ["FEATURE_LANDING"]}
            ],
            commit_type=CommitType.REGULAR_COMMIT,
        )
        assert calls == []


class TestPerformHookBracketsCommandFailure:
    def test_allowed_failure_warns_and_continues(self):
        _, calls, _ = _run(
            "pre-commit",
            True,
            pre_commit_lead=[
                {"cmd": "false", "allow_failure": True},
                {"cmd": "echo next"},
            ],
            run_returncodes=[1, 0],
        )
        assert calls == [
            mock.call("false", shell=True, cwd="/repo"),
            mock.call("echo next", shell=True, cwd="/repo"),
        ]

    def test_disallowed_failure_raises_system_exit_with_returncode(self):
        with pytest.raises(SystemExit) as ei:
            _run(
                "pre-commit",
                True,
                pre_commit_lead=[{"cmd": "false"}],
                run_returncodes=[7],
            )
        assert ei.value.code == 7

    def test_disallowed_failure_stops_remaining_commands(self):
        with mock.patch(
            "hupy.hb.perform_hook_brackets.load_hupy_config",
            return_value=load_config_fixture(
                overrides={
                    "hb": {
                        "is_disabled": False,
                        "pre_commit": {
                            "lead": [
                                {"cmd": "echo first"},
                                {"cmd": "false"},
                                {"cmd": "echo third"},
                            ],
                            "trail": [],
                        },
                        "prepare_commit_msg": {"lead": [], "trail": []},
                    }
                }
            ),
        ), mock.patch(
            "hupy.should_run_module.load_hupy_config",
            return_value=load_config_fixture(),
        ), mock.patch(
            "hupy.hb.perform_hook_brackets.get_current_commit_type",
            return_value=CommitType.REGULAR_COMMIT,
        ), mock.patch(
            "hupy.hb.perform_hook_brackets.subprocess.run",
            side_effect=[_result(0), _result(1), _result(0)],
        ) as run_mock:
            with pytest.raises(SystemExit):
                perform_hook_brackets(
                    _REPO, HupyStateFile(), "pre-commit", True
                )

        assert run_mock.call_args_list == [
            mock.call("echo first", shell=True, cwd="/repo"),
            mock.call("false", shell=True, cwd="/repo"),
        ]
