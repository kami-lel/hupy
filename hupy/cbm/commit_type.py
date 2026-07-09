"""
commit_type.py

commit type flag: categorize git commits by merge strategy
"""

from enum import Flag, auto

from hupy import PROJ_LOGGER_NAME

__all__ = ("CommitType", "CBM_LOGGER_NAME")

CBM_LOGGER_NAME = PROJ_LOGGER_NAME + ".CBM"


MAIN_BRANCH = "main"
DEV_BRANCH = "dev"


class CommitType(Flag):
    """
    represent the type of an in-progress git commit with two-level
    hierarchy: level 1 distinguishes merges from other commits;
    level 2 further categorizes merges by source and target branch.

    See `docs/cbm_doc.md` for detailed descriptions of each merge type.
    """

    _FEATURE_LANDING = auto()
    _VERSION_RELEASE = auto()
    _SYNC_BACKPORT = auto()
    _CATCH_UP = auto()
    _HOTFIX_RELEASE = auto()
    _HOTFIX_BACKPORT = auto()
    _RELEASE_CUT = auto()
    _RELEASE_BACKPORT = auto()
    _OTHER_MERGE = auto()

    # Public Member  -----------------------------------------------------------

    MERGE = auto()
    OTHER_COMMIT = auto()

    FEATURE_LANDING = MERGE | _FEATURE_LANDING
    VERSION_RELEASE = MERGE | _VERSION_RELEASE
    SYNC_BACKPORT = MERGE | _SYNC_BACKPORT
    CATCH_UP = MERGE | _CATCH_UP
    HOTFIX_RELEASE = MERGE | _HOTFIX_RELEASE
    HOTFIX_BACKPORT = MERGE | _HOTFIX_BACKPORT
    RELEASE_CUT = MERGE | _RELEASE_CUT
    RELEASE_BACKPORT = MERGE | _RELEASE_BACKPORT
    OTHER_MERGE = MERGE | _OTHER_MERGE
