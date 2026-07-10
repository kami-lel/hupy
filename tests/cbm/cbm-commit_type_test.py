"""
cbm-commit_type_test.py

tests for `CommitType.decide_commit_type` in `commit_type.py`
"""

import pytest

from hupy.cbm.branch_type import BranchType
from hupy.cbm.commit_type import CommitType

# tests  ########################################################################


class TestDecideCommitTypeKnownPairs:
    @pytest.mark.parametrize(
        "source, target, expected",
        [
            (BranchType.FEATURE, BranchType.DEV, CommitType.FEATURE_LANDING),
            (BranchType.DEV, BranchType.MAIN, CommitType.VERSION_RELEASE),
            (BranchType.MAIN, BranchType.DEV, CommitType.SYNC_BACKPORT),
            (BranchType.DEV, BranchType.FEATURE, CommitType.CATCH_UP),
            (BranchType.HOTFIX, BranchType.MAIN, CommitType.HOTFIX_RELEASE),
            (BranchType.HOTFIX, BranchType.DEV, CommitType.HOTFIX_BACKPORT),
            (BranchType.RELEASE, BranchType.MAIN, CommitType.RELEASE_CUT),
            (BranchType.RELEASE, BranchType.DEV, CommitType.RELEASE_BACKPORT),
        ],
    )
    def test_known_pair_maps_to_expected_type(self, source, target, expected):
        assert CommitType.decide_commit_type(source, target) == expected

    @pytest.mark.parametrize(
        "expected",
        [
            CommitType.FEATURE_LANDING,
            CommitType.VERSION_RELEASE,
            CommitType.SYNC_BACKPORT,
            CommitType.CATCH_UP,
            CommitType.HOTFIX_RELEASE,
            CommitType.HOTFIX_BACKPORT,
            CommitType.RELEASE_CUT,
            CommitType.RELEASE_BACKPORT,
        ],
    )
    def test_known_pair_result_is_a_merge(self, expected):
        assert CommitType.MERGE in expected


class TestDecideCommitTypeUnknownPairs:
    @pytest.mark.parametrize(
        "source, target",
        [
            (BranchType.USER, BranchType.DEV),
            (BranchType.DEV, BranchType.USER),
            (BranchType.FEATURE, BranchType.FEATURE),
            (BranchType.FEATURE, BranchType.MAIN),
            (BranchType.MAIN, BranchType.MAIN),
            (BranchType.MAIN, BranchType.FEATURE),
            (BranchType.DEV, BranchType.DEV),
            (BranchType.DEV, BranchType.HOTFIX),
            (BranchType.HOTFIX, BranchType.HOTFIX),
            (BranchType.HOTFIX, BranchType.FEATURE),
            (BranchType.RELEASE, BranchType.RELEASE),
            (BranchType.RELEASE, BranchType.FEATURE),
            (BranchType.RELEASE, BranchType.HOTFIX),
            (BranchType.USER, BranchType.USER),
            (None, None),
            (None, BranchType.DEV),
            (BranchType.DEV, None),
        ],
    )
    def test_unknown_pair_is_other_merge(self, source, target):
        assert (
            CommitType.decide_commit_type(source, target)
            == CommitType.OTHER_MERGE
        )
