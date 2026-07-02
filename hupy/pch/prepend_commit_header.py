"""
prepend_commit_header.py

prepend commit type header to commit message
"""

from hupy.kamilog import getLogger
from . import PCH_LOGGER_NAME
from ..commit_type import CommitType, get_current_commit_type

# logger  ######################################################################
logger = getLogger(PCH_LOGGER_NAME)


# helpers  #####################################################################


def _prepend_commit_header_by_type(is_feature_finish):
    # TODO implement commit header prepending
    pass


# Public API  ##################################################################


def prepend_commit_header(repo_root):
    """
    prepend commit type header to the current commit message.


    :param repo_root: path to the git repository or any of its subdirectories
    :type repo_root: str
    """
    logger.enter("prepending commit header")

    commit_type = get_current_commit_type(repo_root)

    if CommitType.FEATURE_FINISH in commit_type:
        logger.info("prepending header on Feature Finish merge")
        _prepend_commit_header_by_type(is_feature_finish=True)

    elif CommitType.VERSION_RELEASE in commit_type:
        logger.info("prepending header on Version Release merge")
        _prepend_commit_header_by_type(is_feature_finish=False)

    else:
        logger.skip("regular commit/merge")
        return

    logger.pass_("commit header prepended")
