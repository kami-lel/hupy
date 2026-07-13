"""
state-reset-for-next-commit_test.py

tests for `HupyStateFile.reset_for_next_commit` in `state_file.py`
"""

from hupy.state.state_file import HupyStateFile

# tests  ########################################################################


class TestResetForNextCommit:
    def test_empties_the_flag_set(self):
        state = HupyStateFile(skip_once={"bdc", "ttg"})
        state.reset_for_next_commit()
        assert state.skip_once == set()

    def test_no_op_when_already_empty(self):
        state = HupyStateFile()
        state.reset_for_next_commit()
        assert state.skip_once == set()
