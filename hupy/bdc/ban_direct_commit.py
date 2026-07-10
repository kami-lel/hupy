"""
ban_direct_commit.py

block commits made directly on protected branches
"""

from hupy.kamilog import getLogger
from . import BDC_LOGGER_NAME

# logger  ######################################################################
logger = getLogger(BDC_LOGGER_NAME)
logger.propagate = False


# Public API  ##################################################################
def ban_direct_commit(repo):
    """
    block the current commit if it directly targets a protected
    branch.


    :param repo: git repository object
    :type repo: git.Repo
    """
    logger.enter("perform Ban Direct Commit")
    # TODO implement direct-commit ban
    pass
