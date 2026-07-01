"""
tt_gating.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import getLogger
from .commit_type import CommitType, get_current_commit_type
from .tt_detect import TriageTagType, detect_triage_tags_in_staged_file

logger = getLogger(PROJ_LOGGER_NAME + ".TTG")


# helpers  #####################################################################


def _perform_triage_tags_by_filtering_group(filtering_tt_group):
    pass  # TODO


# Public API  ##################################################################


def perform_triage_tags_gating(repo_root):
    """
    execute triage tag gating for the current commit.


    :param repo_root: path to the git repository or any of its
            subdirectories
    :type repo_root: str
    """
    logger.enter("perform TTG")

    commit_type = get_current_commit_type(repo_root)
    # pylint: disable-next=logging-format-interpolation
    logger.debug("commit type={}".format(commit_type))

    if CommitType.FEATURE_FINISH in commit_type:
        logger.debug("on Feature Finish")
        _perform_triage_tags_by_filtering_group(TriageTagType.LOUDS)

    elif CommitType.VERSION_RELEASE in commit_type:
        logger.debug("on Version Release")
        _perform_triage_tags_by_filtering_group(
            TriageTagType.LOUDS | TriageTagType.STEADYS
        )

    else:
        logger.skip("irrelevant commit/merge type")
        return

    logger.pass_("finish TTG")
