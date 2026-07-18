"""
stub-names-by-demand_test.py

tests for `get_hook_names_by_demand`: with no config file, exactly
the hook stages carrying their own `run_features`/`run_after` are
demanded — including `pre-rebase` and `pre-applypatch`, which carry
Ban Direct Commit
"""

from hupy.stub.names_by_demand import get_hook_names_by_demand

# tests  ########################################################################


class TestGetHookNamesByDemandNoConfig:
    def test_demands_every_stage_with_its_own_features(self, repo):
        names = get_hook_names_by_demand(repo)

        assert sorted(names) == sorted(
            [
                "pre-commit",
                "prepare-commit-msg",
                "pre-merge-commit",
                "pre-rebase",
                "pre-applypatch",
            ]
        )

    def test_demands_pre_rebase_for_ban_direct_commit(self, repo):
        names = get_hook_names_by_demand(repo)

        assert "pre-rebase" in names
