"""
cbm-grct-get_source_branch_test.py

tests for `get_source_branch` in `get_current_commit_type.py`
"""

from . import (
    clone_repo,
    commit_file,
    prepare_merge_repo,
    sha_of,
    write_merge_head,
)

from hupy.cbm.get_current_commit_type import get_source_branch

# tests  ########################################################################


class TestGetSourceBranchBranchTip:
    def test_resolves_to_branch_at_tip(self, repo):
        # `repo` fixture: Feature Landing merge, add-user-authentication -> dev
        assert get_source_branch(repo) == "add-user-authentication"

    def test_resolves_to_whichever_branch_shares_the_tip(self, repo):
        # a second branch pointing at the same commit: any match is
        # acceptable, but it must be one of the two names, not a
        # name-rev fallback string
        sha = sha_of(repo, "add-user-authentication")
        repo.git.branch("mirror", sha)

        assert get_source_branch(repo) in ("add-user-authentication", "mirror")


class TestGetSourceBranchNoBranchTip:
    def test_falls_back_to_name_rev_for_non_tip_commit(self, repo_dir):
        repo = clone_repo(repo_dir)
        repo.git.checkout("-q", "-b", "feature")
        commit_file(repo_dir, "first.py")
        sha_first = sha_of(repo, "feature")
        commit_file(repo_dir, "second.py")  # branch tip moves past sha_first
        repo.git.checkout("-q", "main")
        write_merge_head(repo_dir, sha_first)

        result = get_source_branch(repo)

        assert result != "feature"
        assert isinstance(result, str) and result != ""


class TestGetSourceBranchCaching:
    def test_result_is_cached_across_calls(self, repo, repo_dir):
        first = get_source_branch(repo)
        assert first == "add-user-authentication"

        # MERGE_HEAD now points elsewhere, but the cached value must
        # not change for this repo
        sha_dev = sha_of(repo, "dev")
        write_merge_head(repo_dir, sha_dev)

        second = get_source_branch(repo)
        assert second == first == "add-user-authentication"

    def test_separate_repos_cache_independently(self, tmp_path):
        repo_a = prepare_merge_repo(tmp_path / "repo_a", "feature_landing")
        repo_b = prepare_merge_repo(tmp_path / "repo_b", "regular_merge")

        assert get_source_branch(repo_a) == "add-user-authentication"
        assert get_source_branch(repo_b) == "hotfix"
