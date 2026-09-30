"""
pt-multi-trail_test.py

tests for `perform_paper_trail` iterating several configured Paper
Trail entries: first failure aborts, inapplicable entries are skipped,
and changed files / commit type are read once
"""

import pytest

from hupy.cbm.commit_type import CommitType

# auxiliaries  #################################################################

_PASSING = {"glob": "*.md", "remark": "passing"}
_FAILING = {"glob": "NOTHING-MATCHES-THIS", "remark": "failing"}
_LATER = {"glob": "*.md", "remark": "later"}


def _assert_gated(run_pt, *args, **kwargs):
    with pytest.raises(SystemExit) as exc_info:
        run_pt(*args, **kwargs)
    assert exc_info.value.code == 1


# tests  ########################################################################


class TestMultiplePaperTrails:
    def test_all_satisfied_passes(self, run_pt):
        result = run_pt([_PASSING, _LATER], ["a.md"])
        assert result.logger_mock.pass_.call_count == 2

    def test_first_unsatisfied_aborts(self, run_pt):
        _assert_gated(run_pt, [_FAILING, _PASSING], ["a.md"])

    def test_abort_stops_later_paper_trails(self, run_pt):
        _assert_gated(run_pt, [_FAILING, _LATER], ["a.md"])
        assert run_pt.last.logger_mock.pass_.call_count == 0

    def test_inapplicable_unsatisfied_entry_does_not_block_others(
        self, run_pt
    ):
        inapplicable = dict(_FAILING, allow_commit_types=["VERSION_RELEASE"])
        result = run_pt(
            [inapplicable, _PASSING],
            ["a.md"],
            commit_type=CommitType.REGULAR_COMMIT,
        )
        result.logger_mock.skip.assert_called_once()
        result.logger_mock.pass_.assert_called_once()

    def test_files_and_commit_type_read_once(self, run_pt):
        result = run_pt([_PASSING, _LATER, _PASSING], ["a.md"])
        assert result.paths_mock.call_count == 1
        assert result.type_mock.call_count == 1
