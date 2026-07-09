"""
ver_grep package

extract a repo's version string by regex-matching a line in a
configured version file
"""

from hupy import PROJ_LOGGER_NAME

VER_GREP_LOGGER_NAME = PROJ_LOGGER_NAME + ".VerGrep"

from .gcv import grep_current_version
from .gsbv import grep_source_branch_version

__all__ = ("grep_current_version", "grep_source_branch_version")
