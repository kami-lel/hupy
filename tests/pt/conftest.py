"""
conftest.py

pytest fixtures shared across the `tests/pt/` suite
"""

from types import SimpleNamespace
from unittest import mock

import pytest

from config_fixture import load_config_fixture

from hupy.cbm.commit_type import CommitType
from hupy.pt.perform_paper_trail import perform_paper_trail
from hupy.state.state_file import HupyStateFile

_TARGET = "hupy.pt.perform_paper_trail."

# fixtures  #####################################################################


@pytest.fixture
def run_pt():
    """
    :return: a runner calling `perform_paper_trail` with the repo,
            config, changed paths, commit type, and logger all stubbed
    :rtype: callable
    """

    def _run_pt(
        paper_trails,
        changed_paths,
        commit_type=CommitType.REGULAR_COMMIT,
        is_disabled=False,
        skip_once=(),
    ):
        config = load_config_fixture(
            overrides={
                "pt": {
                    "is_disabled": is_disabled,
                    "trails": list(paper_trails),
                }
            }
        )
        state_file = HupyStateFile(skip_once=set(skip_once))
        with mock.patch(
            _TARGET + "load_hupy_config", return_value=config
        ), mock.patch(
            "hupy.should_run_module.load_hupy_config", return_value=config
        ), mock.patch(
            _TARGET + "get_current_commit_type", return_value=commit_type
        ) as type_mock, mock.patch(
            _TARGET + "get_changed_file_paths", return_value=changed_paths
        ) as paths_mock, mock.patch(
            _TARGET + "logger"
        ) as logger_mock:
            # kept on the runner so mocks stay inspectable after an abort
            _run_pt.last = SimpleNamespace(
                paths_mock=paths_mock,
                type_mock=type_mock,
                logger_mock=logger_mock,
                state_file=state_file,
            )
            perform_paper_trail(SimpleNamespace(), state_file, "pre-commit")
        return _run_pt.last

    _run_pt.last = None
    return _run_pt
