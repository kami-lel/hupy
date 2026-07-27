"""
ver_grep package

extract a repo's version string by regex-matching a line in a
configured version file
"""

# Bug vg uniform test always check HEAD thus wrong

from hupy import PROJ_LOGGER_NAME

VER_GREP_LOGGER_NAME = PROJ_LOGGER_NAME + ".VG"

from .version_bump import decide_version_update_type
from .branch_version import (
    grep_source_branch_version,
    grep_target_branch_version,
)
from .version_uniformity import check_version_uniformity

__all__ = (
    "check_version_uniformity",
    "decide_version_update_type",
    "grep_source_branch_version",
    "grep_target_branch_version",
)
