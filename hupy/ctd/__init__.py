"""
CTD module: identify in-progress commit types
"""

from hupy import PROJ_LOGGER_NAME
from hupy.ctd.commit_type import CommitType
from hupy.ctd.get_current_commit_type import (
	get_current_commit_type,
	get_source_branch,
)

CTD_LOGGER_NAME = PROJ_LOGGER_NAME + ".CTD"

__all__ = (
	"CommitType",
	"get_current_commit_type",
	"get_source_branch",
	"CTD_LOGGER_NAME",
)
