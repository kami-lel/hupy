"""
chain-policy_test.py

tests for the chain-session policy helpers in `cli/chain_policy.py`:
terminal detection, session adoption, and amend detection
"""

import pytest

from hupy.cli.chain_policy import (
    TERMINAL_ALWAYS,
    adopt_session,
    detect_amend,
    is_chain_terminal,
)
from hupy.state.state_file import ChainSession

# tests  ########################################################################


class TestIsChainTerminal:
    @pytest.mark.parametrize(
        "hook_name",
        ["post-merge", "post-applypatch", "post-rewrite", "post-checkout"],
    )
    def test_unconditional_terminals_close(self, hook_name):
        assert is_chain_terminal(hook_name, ChainSession()) is True

    @pytest.mark.parametrize(
        "hook_name", ["pre-commit", "prepare-commit-msg", "commit-msg"]
    )
    def test_mid_chain_stages_do_not_close(self, hook_name):
        assert is_chain_terminal(hook_name, ChainSession()) is False

    def test_post_commit_closes_a_normal_commit(self):
        session = ChainSession(expect_post_rewrite=False)
        assert is_chain_terminal("post-commit", session) is True

    def test_post_commit_yields_on_amend(self):
        session = ChainSession(expect_post_rewrite=True)
        assert is_chain_terminal("post-commit", session) is False

    def test_every_standalone_hook_is_terminal(self):
        for hook_name in TERMINAL_ALWAYS:
            assert is_chain_terminal(hook_name, ChainSession()) is True


class TestAdoptSession:
    def test_fresh_chain_adopts_owner(self):
        session = ChainSession()
        assert adopt_session(session, 100) is True
        assert session.chain_ppid == 100

    def test_same_owner_continues_chain(self):
        session = ChainSession(chain_ppid=100, expect_post_rewrite=True)
        assert adopt_session(session, 100) is False
        # continuation must not wipe a pending amend flag
        assert session.expect_post_rewrite is True

    def test_differing_owner_reclaims_stale_session(self):
        session = ChainSession(chain_ppid=100, expect_post_rewrite=True)
        assert adopt_session(session, 200) is True
        assert session.chain_ppid == 200
        assert session.expect_post_rewrite is False


class TestDetectAmend:
    def test_amend_source_commit_is_detected(self):
        assert detect_amend([".git/COMMIT_EDITMSG", "commit", "HEAD"]) is True

    @pytest.mark.parametrize("source", ["message", "template", "merge", "squash"])
    def test_other_sources_are_not_amend(self, source):
        assert detect_amend([".git/COMMIT_EDITMSG", source]) is False

    def test_bare_editor_commit_is_not_amend(self):
        assert detect_amend([".git/COMMIT_EDITMSG"]) is False

    def test_empty_args_are_not_amend(self):
        assert detect_amend([]) is False
