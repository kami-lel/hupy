"""
ver_grep package

extract a repo's version string by regex-matching a line in a
configured version file
"""

from hupy import PROJ_LOGGER_NAME

VER_GREP_LOGGER_NAME = PROJ_LOGGER_NAME + ".VerGrep"

from .version_bump import decide_version_update_type
from .branch_version import (
    grep_source_branch_version,
    grep_target_branch_version,
    verify_version_grep,
)

__all__ = (
    "decide_version_update_type",
    "grep_source_branch_version",
    "grep_target_branch_version",
    "verify_version_grep",
)
