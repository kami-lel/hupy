"""
ttg-gate-tt-regular-merge_test.py

tests for `perform_triage_tags_gating` on merges between unrelated,
non-protected branches
"""

import git

from hupy.state.state_file import HupyStateFile
from hupy.ttg.gate_tt import perform_triage_tags_gating
from prep_repo import prepare_repo_with_files

_STATE_FILE = HupyStateFile()

_BUCKET = "regular_merge"


# tests  ########################################################################


class TestRegularMerge:
    def test_single_file_with_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir, _BUCKET, {"hotfix.py": "tt_loud_only.py"}
        )
        perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)

    def test_single_file_without_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir, _BUCKET, {"hotfix.py": "tt_none.py"}
        )
        perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)

    def test_multiple_files_none_have_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir,
            _BUCKET,
            {"a.py": "tt_none.py", "b.py": "tt_none.py"},
        )
        perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)

    def test_multiple_files_mixed_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir,
            _BUCKET,
            {"a.py": "tt_loud_only.py", "b.py": "tt_none.py"},
        )
        perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)
