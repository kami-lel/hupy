"""
branch_type.py

define the ``branch-type`` accessor key's ``run_get`` and
``run_info``
"""

from hupy.cbm.branch_type import BranchType
from hupy.cbm.get_current_commit_type import get_target_branch
from hupy.config_file.load_config import load_hupy_config

# constants  ###################################################################
KEY = "branch-type"
DOC = "get the current branch's type"


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the current branch's :class:`BranchType` name.
    """
    branch_name = get_target_branch(repo)
    if branch_name is None:
        logger.error("detached HEAD: no current branch")
        raise SystemExit(1)

    cbm_config = load_hupy_config(repo).cbm
    branch_type = BranchType.from_name(branch_name, cbm_config)
    print(branch_type.name)


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``branch-type`` key.
    """
    print("""{}

value is one of:
FEATURE, DEV, MAIN, HOTFIX, RELEASE, USER
(decided by the current branch's name against the cbm config section)

usage:
  $ hupy get branch-type""".format(DOC))
