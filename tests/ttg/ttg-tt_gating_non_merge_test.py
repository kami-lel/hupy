"""
ttg-tt_gating_non_merge_test.py

tests for `perform_triage_tags_gating` on regular, non-merge commits
"""

from hupy.ttg.tt_gating import perform_triage_tags_gating
from prep_repo import prepare_repo_with_files

_BUCKET = "non_merge_commit"


# tests  ########################################################################


class TestNonMergeCommit:
    def test_single_file_with_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir, _BUCKET, {"feature.py": "tt_loud_only.py"}
        )
        perform_triage_tags_gating(str(repo_dir))

    def test_single_file_without_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir, _BUCKET, {"feature.py": "tt_none.py"}
        )
        perform_triage_tags_gating(str(repo_dir))

    def test_multiple_files_none_have_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir,
            _BUCKET,
            {"a.py": "tt_none.py", "b.py": "tt_none.py"},
        )
        perform_triage_tags_gating(str(repo_dir))

    def test_multiple_files_mixed_tt_is_skipped(self, repo_dir):
        prepare_repo_with_files(
            repo_dir,
            _BUCKET,
            {"a.py": "tt_loud_only.py", "b.py": "tt_none.py"},
        )
        perform_triage_tags_gating(str(repo_dir))
