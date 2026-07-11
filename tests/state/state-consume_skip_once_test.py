"""
state-consume_skip_once_test.py

tests for `HupyStateFile.consume_skip_once` and
`HupyStateFile.reset_for_next_commit` in `state_file.py`
"""

from hupy.state.state_file import HupyStateFile

# tests  ########################################################################


class TestConsumeSkipOnceNotFlagged:
    def test_returns_false_when_not_flagged(self):
        state = HupyStateFile()
        assert state.consume_skip_once("bdc") is False

    def test_leaves_other_entries_untouched(self):
        state = HupyStateFile(skip_once={"ttg"})
        assert state.consume_skip_once("bdc") is False
        assert state.skip_once == {"ttg"}


class TestConsumeSkipOnceFlagged:
    def test_returns_true_when_flagged(self):
        state = HupyStateFile(skip_once={"bdc"})
        assert state.consume_skip_once("bdc") is True

    def test_does_not_discard_the_flag(self):
        state = HupyStateFile(skip_once={"bdc"})
        state.consume_skip_once("bdc")
        assert "bdc" in state.skip_once

    def test_leaves_sibling_entries_untouched(self):
        state = HupyStateFile(skip_once={"bdc", "ttg"})
        state.consume_skip_once("bdc")
        assert state.skip_once == {"bdc", "ttg"}

    def test_second_call_still_returns_true(self):
        state = HupyStateFile(skip_once={"bdc"})
        state.consume_skip_once("bdc")
        assert state.consume_skip_once("bdc") is True


class TestResetForNextCommit:
    def test_empties_the_flag_set(self):
        state = HupyStateFile(skip_once={"bdc", "ttg"})
        state.reset_for_next_commit()
        assert state.skip_once == set()

    def test_no_op_when_already_empty(self):
        state = HupyStateFile()
        state.reset_for_next_commit()
        assert state.skip_once == set()
