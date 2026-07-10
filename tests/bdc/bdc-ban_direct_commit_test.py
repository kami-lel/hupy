"""
bdc-ban_direct_commit_test.py

tests for `ban_direct_commit` in `ban_direct_commit.py`
"""

from unittest import mock

import pytest

from hupy.bdc.ban_direct_commit import ban_direct_commit
from hupy.cbm import CommitType
from hupy.config.config_file import HupyConfigFile

_REPO = object()


# helpers  ######################################################################


def _run(
    current_branch,
    commit_type,
    ban_commit_to_dev=True,
    ban_commit_to_main=True,
    ban_commit_to_branches=(),
    dev_branch_name="dev",
    main_branch_name="main",
):
    """
    run ``ban_direct_commit`` against a stubbed config and stubbed
    ``cbm`` lookups, bypassing disk/git config loading.
    """
    config = HupyConfigFile(
        cbm={
            "dev_branch_name": dev_branch_name,
            "main_branch_name": main_branch_name,
        },
        bdc={
            "ban_commit_to_dev": ban_commit_to_dev,
            "ban_commit_to_main": ban_commit_to_main,
            "ban_commit_to_branches": list(ban_commit_to_branches),
        },
    )
    with mock.patch(
        "hupy.bdc.ban_direct_commit.load_hupy_config", return_value=config
    ), mock.patch(
        "hupy.bdc.ban_direct_commit.get_target_branch",
        return_value=current_branch,
    ), mock.patch(
        "hupy.bdc.ban_direct_commit.get_current_commit_type",
        return_value=commit_type,
    ):
        return ban_direct_commit(_REPO)


# tests  ########################################################################


class TestBanDirectCommitUnprotectedBranch:
    def test_branch_not_in_any_protected_set_is_skipped(_):
        assert _run("feature/x", CommitType.OTHER_COMMIT) is None

    def test_dev_branch_skipped_when_ban_commit_to_dev_disabled(_):
        assert (
            _run(
                "dev",
                CommitType.OTHER_COMMIT,
                ban_commit_to_dev=False,
            )
            is None
        )

    def test_main_branch_skipped_when_ban_commit_to_main_disabled(_):
        assert (
            _run(
                "main",
                CommitType.OTHER_COMMIT,
                ban_commit_to_main=False,
            )
            is None
        )

    def test_detached_head_target_branch_is_skipped(_):
        assert _run(None, CommitType.OTHER_COMMIT) is None


class TestBanDirectCommitProtectedBranchSources:
    def test_dev_branch_name_from_cbm_config_is_protected(_):
        with pytest.raises(SystemExit):
            _run(
                "develop",
                CommitType.OTHER_COMMIT,
                dev_branch_name="develop",
            )

    def test_main_branch_name_from_cbm_config_is_protected(_):
        with pytest.raises(SystemExit):
            _run(
                "trunk",
                CommitType.OTHER_COMMIT,
                main_branch_name="trunk",
            )

    def test_explicit_ban_commit_to_branches_entry_is_protected(_):
        with pytest.raises(SystemExit):
            _run(
                "release/1.0",
                CommitType.OTHER_COMMIT,
                ban_commit_to_dev=False,
                ban_commit_to_main=False,
                ban_commit_to_branches=["release/1.0"],
            )


class TestBanDirectCommitOnProtectedBranch:
    def test_non_merge_commit_raises_system_exit(_):
        with pytest.raises(SystemExit) as ei:
            _run("main", CommitType.OTHER_COMMIT)
        assert ei.value.code == 1

    def test_feature_landing_merge_commit_is_allowed(_):
        assert _run("dev", CommitType.FEATURE_LANDING) is None

    def test_version_release_merge_commit_is_allowed(_):
        assert _run("main", CommitType.VERSION_RELEASE) is None

    def test_other_merge_commit_is_allowed(_):
        assert _run("main", CommitType.OTHER_MERGE) is None
