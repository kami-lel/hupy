"""
CBM module: identify commit, branch, and merge types
"""

from hupy import PROJ_LOGGER_NAME
from hupy.cbm.branch_type import BranchType
from hupy.cbm.commit_type import CommitType

CBM_LOGGER_NAME = PROJ_LOGGER_NAME + ".CBM"

__all__ = (
    "BranchType",
    "CommitType",
    "CBM_LOGGER_NAME",
)
