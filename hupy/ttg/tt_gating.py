"""
tt_gating.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

import re
import subprocess
import sys

from hupy.kamilog import AnsiRenderer, getLogger, gen_comment_banner_centered
from hupy.config.load_config import load_hupy_config
from ..ttg import TTG_LOGGER_NAME
from ..cbm import CommitType, get_current_commit_type
from .tt_detect import (
    _TT_PATTERN,
    TriageTagType,
    detect_triage_tags_in_staged_file,
)

# logger  ######################################################################
logger = getLogger(TTG_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


def _perform_triage_tags_by_filtering_group(repo, filtering_tt_group):
    try:
        cached_files = (
            subprocess.check_output(
                ("git", "diff", "--cached", "--name-only"),
                text=True,
                stderr=subprocess.PIPE,
                cwd=repo.working_dir,
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
            file_path, repo_root=repo.working_dir
        )
        filtered = TriageTagType.filter_by_group(
            [tag for tag, _, _ in tags_in_file],
            filtering_tt_group,
        )

        if filtered:
            filtered_results[file_path] = [
                (tag, line, line_no)
                for tag, line, line_no in tags_in_file
                if tag in filtered
            ]

    if filtered_results:
        logger.fail("gated Triage Tags found")
        renderer = AnsiRenderer(sys.stdout)
        msg_lines = [""]
        for file_path, results in filtered_results.items():
            msg_lines.append(gen_comment_banner_centered(file_path, "-"))
            line_no_width = max(len(str(line_no)) for _, _, line_no in results)
            for _, line, line_no in results:
                line_no_str = renderer.color_grey(
                    str(line_no).rjust(line_no_width)
                )
                stripped_line = line.strip()
                match = re.search(_TT_PATTERN, stripped_line)
                if match:
                    colored_tag = renderer.color_triage_tag(match.group(1))
                    stripped_line = (
                        stripped_line[: match.start()]
                        + colored_tag
                        + stripped_line[match.end() :]
                    )
                msg_lines.append(line_no_str + " " + stripped_line)
        logger.info("\n".join(msg_lines))
        raise SystemExit(1)


# Public API  ##################################################################
def perform_triage_tags_gating(repo):
    """
    execute triage tag gating for the current commit.


    :param repo: git repository object
    :type repo: git.Repo
    """
    config = load_hupy_config(repo)
    if config.ttg.is_disabled:
        logger.skip("Triage Tag Gating disabled")
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


# TODO add config for ignored globs
