"""
gate_tt.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

from hupy.kamilog import getLogger
from hupy.config.load_config import load_hupy_config
from hupy.should_run_module import should_run_module
from ..ttg import TTG_LOGGER_NAME
from ..cbm import CommitType, get_current_commit_type
from .triage_tag_type import TriageTagType
from .detect_tt import detect_triage_tags_in_staged_file
from .staged_files import get_staged_file_paths, is_path_ignored
from .report_tt import report_gated_tags

# logger  ######################################################################
logger = getLogger(TTG_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


def _collect_gated_tags(
    repo,
    cached_files,
    filtering_tt_group,
    ignored_path_globs,
    disable_tt_detect_by_type,
):
    """
    :return: staged file path -> gated ``(tag, line, line_no)`` tuples
    :rtype: dict
    """
    filtered_results = {}

    for file_path in cached_files:
        if is_path_ignored(file_path, ignored_path_globs):
            logger.debug("skip ignored path: " + file_path)
            continue

        tags_in_file = detect_triage_tags_in_staged_file(
            file_path,
            repo_root=repo.working_dir,
            disable_tt_detect_by_type=disable_tt_detect_by_type,
        )
        gated_tags = [
            (tag, line, line_no)
            for tag, line, line_no in tags_in_file
            if tag in filtering_tt_group
        ]

        if gated_tags:
            filtered_results[file_path] = gated_tags

    return filtered_results


def _perform_triage_tags_by_filtering_group(repo, filtering_tt_group):
    config = load_hupy_config(repo)
    cached_files = get_staged_file_paths(repo)
    filtered_results = _collect_gated_tags(
        repo,
        cached_files,
        filtering_tt_group,
        config.ttg.ignored_path_globs,
        config.ttg.disable_tt_detect_by_type,
    )

    if filtered_results:
        report_gated_tags(filtered_results)


# Public API  ##################################################################
def perform_triage_tags_gating(repo, state_file):
    """
    execute triage tag gating for the current commit.


    :param repo: git repository object
    :type repo: git.Repo
    :param state_file: the open HUPy state file, as yielded by
            ``open_state_file``
    :type state_file: HupyStateFile
    """
    if not should_run_module(repo, state_file, "ttg"):
        return

    logger.enter("perform Triage Tag Gating")

    commit_type = get_current_commit_type(repo)

    if CommitType.FEATURE_LANDING in commit_type:
        logger.debug("TTG on Feature Landing merge")
        _perform_triage_tags_by_filtering_group(repo, TriageTagType.LOUDS)

    elif CommitType.VERSION_RELEASE in commit_type:
        logger.debug("TTG on Version Release merge")
        _perform_triage_tags_by_filtering_group(
            repo, TriageTagType.LOUDS | TriageTagType.STEADYS
        )

    else:
        logger.skip("regular commit/merge")
        return

    logger.pass_("no gated TT found")
