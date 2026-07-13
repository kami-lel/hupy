"""
should-run-module_test.py

tests for `should_run_module`, combining a module's config
``is_disabled`` flag with the state file's one-time ``skip_once`` set
"""

from unittest import mock

import pytest

from config_fixture import load_config_fixture

from hupy.should_run_module import should_run_module
from hupy.state.state_file import HupyStateFile

_REPO = object()

_MODULE_ABBRS = ("vg", "ttg", "pch", "bdc", "hb")


# helpers  ######################################################################


def _run(module_abbr, is_disabled=False, skip_once=()):
    """
    run ``should_run_module`` against a stubbed config and state
    file, bypassing disk/git config loading.


    :return: the call's result, and the state file afterward (to
            inspect ``skip_once`` consumption)
    :rtype: tuple[bool, HupyStateFile]
    """
    config = load_config_fixture(
        overrides={module_abbr: {"is_disabled": is_disabled}}
    )
    state_file = HupyStateFile(skip_once=set(skip_once))
    with mock.patch(
        "hupy.should_run_module.load_hupy_config", return_value=config
    ):
        result = should_run_module(_REPO, state_file, module_abbr)
    return result, state_file


# tests  ########################################################################


class TestShouldRunModuleEnabledNotFlagged:
    @pytest.mark.parametrize("module_abbr", _MODULE_ABBRS)
    def test_runs_when_enabled_and_not_flagged(self, module_abbr):
        result, state_file = _run(module_abbr)
        assert result is True
        assert state_file.skip_once == set()


class TestShouldRunModuleDisabled:
    @pytest.mark.parametrize("module_abbr", _MODULE_ABBRS)
    def test_does_not_run_when_disabled(self, module_abbr):
        result, _ = _run(module_abbr, is_disabled=True)
        assert result is False

    def test_disabled_takes_precedence_over_skip_once(self):
        result, _ = _run("bdc", is_disabled=True, skip_once={"bdc"})
        assert result is False

    def test_disabled_does_not_consume_skip_once_flag(self):
        _, state_file = _run("bdc", is_disabled=True, skip_once={"bdc"})
        assert "bdc" in state_file.skip_once


class TestShouldRunModuleSkipOnce:
    @pytest.mark.parametrize("module_abbr", _MODULE_ABBRS)
    def test_does_not_run_when_flagged(self, module_abbr):
        result, _ = _run(module_abbr, skip_once={module_abbr})
        assert result is False

    def test_flag_is_not_consumed(self):
        _, state_file = _run("ttg", skip_once={"ttg"})
        assert "ttg" in state_file.skip_once

    def test_only_matching_module_is_flagged(self):
        _, state_file = _run("bdc", skip_once={"bdc", "ttg"})
        assert state_file.skip_once == {"bdc", "ttg"}

    def test_second_call_within_round_still_skips(self):
        config = load_config_fixture(overrides={"pch": {"is_disabled": False}})
        state_file = HupyStateFile(skip_once={"pch"})
        with mock.patch(
            "hupy.should_run_module.load_hupy_config", return_value=config
        ):
            first = should_run_module(_REPO, state_file, "pch")
            second = should_run_module(_REPO, state_file, "pch")
        assert first is False
        assert second is False

    def test_runs_again_after_round_cleared(self):
        config = load_config_fixture(overrides={"pch": {"is_disabled": False}})
        state_file = HupyStateFile(skip_once={"pch"})
        with mock.patch(
            "hupy.should_run_module.load_hupy_config", return_value=config
        ):
            first = should_run_module(_REPO, state_file, "pch")
            state_file.reset_for_next_commit()
            second = should_run_module(_REPO, state_file, "pch")
        assert first is False
        assert second is True
