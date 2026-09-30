"""
pt-skip_test.py

tests for the early returns of `perform_paper_trail`: module disabled,
one-time skip flag, and no Paper Trail configured
"""

import pytest

# auxiliaries  #################################################################

_UNSATISFIABLE = [{"glob": "NOTHING-MATCHES-THIS"}]


def _assert_gated(run_pt, *args, **kwargs):
    with pytest.raises(SystemExit) as exc_info:
        run_pt(*args, **kwargs)
    assert exc_info.value.code == 1


# tests  ########################################################################


class TestPerformPaperTrailSkips:
    def test_pt_disabled_skips_and_reads_nothing(self, run_pt):
        result = run_pt(_UNSATISFIABLE, ["a.py"], is_disabled=True)
        result.paths_mock.assert_not_called()

    def test_skip_once_flag_skips_and_stays_flagged(self, run_pt):
        result = run_pt(_UNSATISFIABLE, ["a.py"], skip_once={"pt"})
        result.paths_mock.assert_not_called()
        assert "pt" in result.state_file.skip_once

    def test_skip_once_with_unrelated_key_runs_normally(self, run_pt):
        _assert_gated(run_pt, _UNSATISFIABLE, ["a.py"], skip_once={"bdc"})

    def test_no_paper_trail_configured_skips_before_reading_files(
        self, run_pt
    ):
        result = run_pt([], ["a.py"])
        result.paths_mock.assert_not_called()
        result.logger_mock.skip.assert_called_once()
