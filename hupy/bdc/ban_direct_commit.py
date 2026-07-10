"""
ban_direct_commit.py

block commits made directly on protected branches
"""

from hupy.config.load_config import load_hupy_config
from hupy.kamilog import getLogger
from ..cbm import CommitType, get_current_commit_type, get_target_branch
from . import BDC_LOGGER_NAME

# logger  ######################################################################
logger = getLogger(BDC_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


def _get_protected_branches(repo):
    """
    build the set of protected branch names from the ``cbm``/``bdc``
    config sections
    """
    config = load_hupy_config(repo)
    protected_branches = set(config.bdc.ban_commit_to_branches)
    if config.bdc.ban_commit_to_dev:
        protected_branches.add(config.cbm.dev_branch_name)
    if config.bdc.ban_commit_to_main:
        protected_branches.add(config.cbm.main_branch_name)
    return protected_branches


# Public API  ##################################################################
def ban_direct_commit(repo):
    """
    block the current commit if it directly targets a protected
    branch.


    :param repo: git repository object
    :type repo: git.Repo
    """
    logger.enter("perform Ban Direct Commit")

    current_branch = get_target_branch(repo)

    if current_branch not in _get_protected_branches(repo):
        logger.skip("not a protected branch")
        return

    commit_type = get_current_commit_type(repo)

    if CommitType.MERGE in commit_type:
        logger.succ("merge into protected branch")
        return

    logger.fail("attempt direct commit to protected branch")
    raise SystemExit(1)
