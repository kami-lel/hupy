"""
tt_gating.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

from .commit_type import CommitType, get_current_commit_type
from .kamilog import getLogger

logger = getLogger("hupy TTG")


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
    logger.debug("find commit type={}".format(commit_type))

    if CommitType.FEATURE_FINISH in commit_type:
        pass  # TODO

    elif CommitType.VERSION_RELEASE in commit_type:
        pass  # TODO

    else:
        logger.skip("irrelevant commit/merge type")
        return

    logger.pass_("finish TTG")
