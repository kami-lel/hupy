"""
state-reset-for-next-commit_test.py

tests for `HupyStateFile.reset_for_next_chain` and `ChainSession` in
`state_file.py`
"""

from hupy.state.state_file import ChainSession, HupyStateFile

# tests  ########################################################################


class TestResetForNextChain:
    def test_empties_the_flag_set(self):
        state = HupyStateFile(skip_once={"bdc", "ttg"})
        state.reset_for_next_chain()
        assert state.skip_once == set()

    def test_no_op_when_already_empty(self):
        state = HupyStateFile()
        state.reset_for_next_chain()
        assert state.skip_once == set()

    def test_forgets_the_chain_session(self):
        state = HupyStateFile(
            chain_session=ChainSession(
                chain_ppid=4242, expect_post_rewrite=True
            )
        )
        state.reset_for_next_chain()
        assert state.chain_session.chain_ppid is None
        assert state.chain_session.expect_post_rewrite is False


class TestChainSession:
    def test_defaults_are_idle(self):
        session = ChainSession()
        assert session.chain_ppid is None
        assert session.expect_post_rewrite is False
        assert session.is_active() is False

    def test_is_active_when_owner_set(self):
        session = ChainSession(chain_ppid=4242)
        assert session.is_active() is True

    def test_reset_clears_owner_and_flag(self):
        session = ChainSession(chain_ppid=4242, expect_post_rewrite=True)
        session.reset()
        assert session.chain_ppid is None
        assert session.expect_post_rewrite is False
