"""
pt-match_test.py

tests for glob matching and logging in `perform_paper_trail`: a Paper
Trail passes iff some changed path matches its glob, else exit code 1
"""

import pytest

# auxiliaries  #################################################################


def _assert_gated(run_pt, *args, **kwargs):
    with pytest.raises(SystemExit) as exc_info:
        run_pt(*args, **kwargs)
    assert exc_info.value.code == 1


def _assert_passes(run_pt, *args, **kwargs):
    return run_pt(*args, **kwargs)


# tests  ########################################################################


class TestPerformPaperTrailMatch:
    def test_exact_filename_match_passes(self, run_pt):
        _assert_passes(
            run_pt, [{"glob": "CHANGELOG.md"}], ["CHANGELOG.md", "a.py"]
        )

    def test_wildcard_glob_passes(self, run_pt):
        _assert_passes(run_pt, [{"glob": "*.md"}], ["README.md"])

    def test_no_matching_path_aborts_with_exit_1(self, run_pt):
        _assert_gated(run_pt, [{"glob": "*.md"}], ["a.py"])

    def test_empty_changed_set_aborts(self, run_pt):
        _assert_gated(run_pt, [{"glob": "*.md"}], [])

    def test_any_one_of_many_paths_is_enough(self, run_pt):
        _assert_passes(
            run_pt, [{"glob": "*.md"}], ["a.py", "b.py", "c.md", "d.py"]
        )

    def test_star_crosses_directory_separator(self, run_pt):
        _assert_passes(run_pt, [{"glob": "docs/*.md"}], ["docs/a/b.md"])

    def test_directory_glob_does_not_match_unrelated_dir(self, run_pt):
        _assert_gated(run_pt, [{"glob": "docs/*"}], ["src/a.py"])


class TestPerformPaperTrailLogging:
    def test_satisfied_paper_trail_logs_pass_with_remark(self, run_pt):
        result = run_pt(
            [{"glob": "*.md", "remark": "docs touched"}], ["a.md"]
        )
        result.logger_mock.pass_.assert_called_once()
        message = result.logger_mock.pass_.call_args.args[0]
        assert "docs touched" in message

    def test_unsatisfied_paper_trail_logs_fail_with_remark(self, run_pt):
        with pytest.raises(SystemExit):
            run_pt([{"glob": "*.md", "remark": "docs touched"}], ["a.py"])
        message = run_pt.last.logger_mock.fail.call_args.args[0]
        assert "docs touched" in message

    def test_heading_falls_back_to_glob_without_remark(self, run_pt):
        result = run_pt([{"glob": "*.md"}], ["a.md"])
        message = result.logger_mock.pass_.call_args.args[0]
        assert "*.md" in message
