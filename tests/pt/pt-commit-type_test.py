"""
pt-commit-type_test.py

tests for the `allow_commit_types` filter in `perform_paper_trail`: an
inapplicable Paper Trail is skipped, an applicable one is enforced
"""

import pytest

from hupy.cbm.commit_type import CommitType

# auxiliaries  #################################################################


def _paper_trail(allow):
    return [{"glob": "NOTHING-MATCHES-THIS", "allow_commit_types": allow}]


def _assert_gated(run_pt, *args, **kwargs):
    with pytest.raises(SystemExit) as exc_info:
        run_pt(*args, **kwargs)
    assert exc_info.value.code == 1


# tests  ########################################################################


class TestCommitTypeFilter:
    @pytest.mark.parametrize(
        "commit_type",
        [
            CommitType.REGULAR_COMMIT,
            CommitType.FEATURE_LANDING,
            CommitType.VERSION_RELEASE,
            CommitType.OTHER_MERGE,
        ],
    )
    def test_empty_filter_applies_to_every_commit_type(
        self, run_pt, commit_type
    ):
        _assert_gated(
            run_pt, _paper_trail([]), ["a.py"], commit_type=commit_type
        )

    def test_matching_type_is_enforced(self, run_pt):
        _assert_gated(
            run_pt,
            _paper_trail(["FEATURE_LANDING"]),
            ["a.py"],
            commit_type=CommitType.FEATURE_LANDING,
        )

    def test_matching_type_satisfied_passes(self, run_pt):
        run_pt(
            [{"glob": "*.py", "allow_commit_types": ["FEATURE_LANDING"]}],
            ["a.py"],
            commit_type=CommitType.FEATURE_LANDING,
        )

    def test_non_matching_type_is_skipped_even_if_unsatisfied(self, run_pt):
        result = run_pt(
            _paper_trail(["FEATURE_LANDING"]),
            ["a.py"],
            commit_type=CommitType.REGULAR_COMMIT,
        )
        result.logger_mock.skip.assert_called_once()
        result.logger_mock.fail.assert_not_called()

    @pytest.mark.parametrize(
        "commit_type",
        [CommitType.FEATURE_LANDING, CommitType.VERSION_RELEASE],
    )
    def test_multi_type_filter_enforced_for_each_member(
        self, run_pt, commit_type
    ):
        _assert_gated(
            run_pt,
            _paper_trail(["FEATURE_LANDING", "VERSION_RELEASE"]),
            ["a.py"],
            commit_type=commit_type,
        )

    def test_multi_type_filter_skipped_for_other_type(self, run_pt):
        result = run_pt(
            _paper_trail(["FEATURE_LANDING", "VERSION_RELEASE"]),
            ["a.py"],
            commit_type=CommitType.REGULAR_COMMIT,
        )
        result.logger_mock.skip.assert_called_once()

    @pytest.mark.parametrize(
        "commit_type",
        [CommitType.FEATURE_LANDING, CommitType.CATCH_UP],
    )
    def test_merge_group_filter_enforced_for_any_merge_subtype(
        self, run_pt, commit_type
    ):
        _assert_gated(
            run_pt,
            _paper_trail(["MERGE"]),
            ["a.py"],
            commit_type=commit_type,
        )

    def test_merge_group_filter_skipped_for_non_merge_commit(self, run_pt):
        result = run_pt(
            _paper_trail(["MERGE"]),
            ["a.py"],
            commit_type=CommitType.REGULAR_COMMIT,
        )
        result.logger_mock.skip.assert_called_once()
