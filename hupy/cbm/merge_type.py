"""
merge_type.py

categorize git merges by source and target branches
"""

from enum import Flag, auto

__all__ = ("MergeType",)


class MergeType(Flag):
    """
    represent the type of merge by source and target branches.
    categorizes common merge workflows and release strategies.

    See `docs/cbm_doc.md` for detailed descriptions of each merge type.
    """

    FEATURE_LANDING = auto()
    VERSION_RELEASE = auto()
    SYNC_BACKPORT = auto()
    CATCH_UP = auto()
    HOTFIX_RELEASE = auto()
    HOTFIX_BACKPORT = auto()
    RELEASE_CUT = auto()
    RELEASE_BACKPORT = auto()
