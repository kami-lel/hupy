"""
tt_gating.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

import subprocess

from hupy.kamilog import getLogger, gen_comment_banner_centered
from ..ttg import TTG_LOGGER_NAME
from ..commit_type import CommitType, get_current_commit_type
from .tt_detect import TriageTagType, detect_triage_tags_in_staged_file

# logger  ######################################################################
logger = getLogger(TTG_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


def _perform_triage_tags_by_filtering_group(repo_root, filtering_tt_group):
    try:
        cached_files = (
            subprocess.check_output(
                ("git", "diff", "--cached", "--name-only"),
                text=True,
                stderr=subprocess.PIPE,
                cwd=repo_root,
            )
            .strip()
            .split("\n")
        )
    except subprocess.CalledProcessError as e:
        logger.critical("unable to get git cached files")
        raise SystemExit(1) from e

    filtered_results = {}

    for file_path in cached_files:
        if not file_path:
            continue

        tags_in_file = detect_triage_tags_in_staged_file(
            file_path, repo_root=repo_root
        )
        filtered = TriageTagType.filter_by_group(
            [tag for tag, _ in tags_in_file],
            filtering_tt_group,
        )

        if filtered:
            filtered_results[file_path] = [
                (tag, line) for tag, line in tags_in_file if tag in filtered
            ]

    if filtered_results:
        logger.fail("gated Triage Tags found")
        msg_lines = [""]
        for file_path, results in filtered_results.items():
            msg_lines.append(gen_comment_banner_centered(file_path, "-"))
            for _, line in results:
                # todo print gated TT in colored highlighting
                msg_lines.append(line.strip())
        logger.info("\n".join(msg_lines))
        raise SystemExit(1)


# Public API  ##################################################################


def perform_triage_tags_gating(repo_root):
    """
    execute triage tag gating for the current commit.


    :param repo_root: path to the git repository or any of its
            subdirectories
    :type repo_root: str
    """
    logger.enter("performing TTG")

    commit_type = get_current_commit_type(repo_root)

    if CommitType.FEATURE_FINISH in commit_type:
        logger.debug("TTG on Feature Finish merge")
        _perform_triage_tags_by_filtering_group(repo_root, TriageTagType.LOUDS)

    elif CommitType.VERSION_RELEASE in commit_type:
        logger.debug("TTG on Version Release merge")
        _perform_triage_tags_by_filtering_group(
            repo_root, TriageTagType.LOUDS | TriageTagType.STEADYS
        )

    else:
        logger.skip("regular commit/merge")
        return

    logger.pass_("no gated TT found")
