"""
tt_gating.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

from .. import PROJ_LOGGER_NAME
from ..kamilog import getLogger
from .commit_type import CommitType, get_current_commit_type

logger = getLogger(PROJ_LOGGER_NAME + ".TTG")


# constants  ###################################################################


# TODO
_FEATURE_FINISH_GATING_TT_PATTERN = r""
_VERSION_RELEASE_GATING_TT_PATTERN = r""


# helpers  #####################################################################


def _perform_triage_tags_gating_by_pattern(regex_pattern):
    pass  # TODO


# FIXME opmz logger conditions


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
        _perform_triage_tags_gating_by_pattern(
            _FEATURE_FINISH_GATING_TT_PATTERN
        )

    elif CommitType.VERSION_RELEASE in commit_type:
        logger.debug("on Version Release")
        _perform_triage_tags_gating_by_pattern(
            _VERSION_RELEASE_GATING_TT_PATTERN
        )

    else:
        logger.skip("irrelevant commit/merge type")
        return

    logger.pass_("finish TTG")
