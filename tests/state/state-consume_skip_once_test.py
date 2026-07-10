"""
state-consume_skip_once_test.py

tests for `HupyStateFile.consume_skip_once` in `state_file.py`
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

    def test_discards_the_flag(self):
        state = HupyStateFile(skip_once={"bdc"})
        state.consume_skip_once("bdc")
        assert "bdc" not in state.skip_once

    def test_only_discards_the_matching_entry(self):
        state = HupyStateFile(skip_once={"bdc", "ttg"})
        state.consume_skip_once("bdc")
        assert state.skip_once == {"ttg"}

    def test_second_call_returns_false(self):
        state = HupyStateFile(skip_once={"bdc"})
        state.consume_skip_once("bdc")
        assert state.consume_skip_once("bdc") is False
