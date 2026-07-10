"""
cbm-branch_type_test.py

tests for `BranchType.from_name` in `branch_type.py`
"""

from unittest import mock

from config_fixture import load_config_fixture

from hupy.cbm.branch_type import BranchType

# helpers  ######################################################################


def _classify(branch_name, **cbm_overrides):
    """
    classify ``branch_name`` against a stubbed config carrying
    ``cbm_overrides``, bypassing disk/git config loading.
    """
    config = load_config_fixture(overrides={"cbm": cbm_overrides})
    with mock.patch(
        "hupy.cbm.branch_type.load_hupy_config", return_value=config
    ):
        return BranchType.from_name(branch_name, mock.sentinel.repo)


# tests  ########################################################################


class TestFromNameDefaultConfig:
    def test_dev_branch_is_dev(self):
        assert _classify("dev") == BranchType.DEV

    def test_main_branch_is_main(self):
        assert _classify("main") == BranchType.MAIN

    def test_hotfix_prefixed_branch_is_hotfix(self):
        assert _classify("hotfix/fix-login-crash") == BranchType.HOTFIX

    def test_release_prefixed_branch_is_release(self):
        assert _classify("release/2.4.0") == BranchType.RELEASE

    def test_slashed_branch_is_user(self):
        assert _classify("kami/add-user-authentication") == BranchType.USER

    def test_unslashed_branch_is_feature(self):
        assert _classify("add-user-authentication") == BranchType.FEATURE

    def test_bare_prefix_name_without_slash_is_feature(self):
        # "hotfix"/"release" alone (no trailing "/...") isn't a match:
        # only the "<prefix>/" form counts
        assert _classify("hotfix") == BranchType.FEATURE
        assert _classify("release") == BranchType.FEATURE

    def test_prefix_lookalike_without_slash_is_feature(self):
        # starts with the prefix text but not "<prefix>/"
        assert _classify("hotfixed-thing") == BranchType.FEATURE
        assert _classify("releaseX") == BranchType.FEATURE

    def test_empty_branch_name_is_feature(self):
        assert _classify("") == BranchType.FEATURE


class TestFromNameCustomConfig:
    def test_custom_main_branch_name(self):
        assert (
            _classify("master", main_branch_name="master")
            == BranchType.MAIN
        )
        # default "main" no longer matches once overridden
        assert (
            _classify("main", main_branch_name="master")
            == BranchType.FEATURE
        )

    def test_custom_dev_branch_name(self):
        assert (
            _classify("develop", dev_branch_name="develop") == BranchType.DEV
        )
        assert (
            _classify("dev", dev_branch_name="develop") == BranchType.FEATURE
        )

    def test_custom_hotfix_prefix(self):
        assert (
            _classify("bugfix/x", hotfix_branch_prefix="bugfix")
            == BranchType.HOTFIX
        )
        assert (
            _classify("hotfix/x", hotfix_branch_prefix="bugfix")
            == BranchType.USER
        )

    def test_custom_release_prefix(self):
        assert (
            _classify("rel/2.4.0", release_branch_prefix="rel")
            == BranchType.RELEASE
        )
        assert (
            _classify("release/2.4.0", release_branch_prefix="rel")
            == BranchType.USER
        )


class TestFromNamePrecedence:
    def test_dev_checked_before_slash_fallback(self):
        # dev branch name itself contains a "/"; DEV must win over USER
        assert (
            _classify("team/dev", dev_branch_name="team/dev")
            == BranchType.DEV
        )

    def test_main_checked_before_slash_fallback(self):
        assert (
            _classify("team/main", main_branch_name="team/main")
            == BranchType.MAIN
        )

    def test_dev_checked_before_main(self):
        # if dev and main happen to share a name, dev (checked first) wins
        assert (
            _classify(
                "trunk", dev_branch_name="trunk", main_branch_name="trunk"
            )
            == BranchType.DEV
        )

    def test_hotfix_checked_before_release(self):
        # a branch can't literally match both prefixes at once here,
        # but confirm hotfix's own prefix match isn't shadowed by a
        # release prefix set to the same value
        assert (
            _classify(
                "shared/x",
                hotfix_branch_prefix="shared",
                release_branch_prefix="shared",
            )
            == BranchType.HOTFIX
        )


class TestFromNamePassesRepo:
    def test_repo_forwarded_to_load_hupy_config(self):
        config = load_config_fixture()
        with mock.patch(
            "hupy.cbm.branch_type.load_hupy_config", return_value=config
        ) as mocked:
            BranchType.from_name("dev", mock.sentinel.repo)
        mocked.assert_called_once_with(mock.sentinel.repo)
