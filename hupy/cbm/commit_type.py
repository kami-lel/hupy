"""
commit_type.py

commit type flag: categorize git commits by merge strategy
"""

from enum import Flag, auto

from hupy.cbm.branch_type import BranchType

__all__ = ("CommitType",)


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

    REGULAR_COMMIT = auto()
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

    @classmethod
    def decide_commit_type(cls, source, target):
        """
        :param source: type of the merge's source branch
        :type source: BranchType, optional
        :param target: type of the merge's target branch
        :type target: BranchType, optional
        :return: the merge type matching ``source`` and ``target``,
                or ``OTHER_MERGE`` if the pair matches no known pattern
        :rtype: CommitType
        """
        return _MERGE_TYPE_BY_BRANCH_PAIR.get((source, target), cls.OTHER_MERGE)


_MERGE_TYPE_BY_BRANCH_PAIR = {
    (BranchType.FEATURE, BranchType.DEV): CommitType.FEATURE_LANDING,
    (BranchType.DEV, BranchType.MAIN): CommitType.VERSION_RELEASE,
    (BranchType.MAIN, BranchType.DEV): CommitType.SYNC_BACKPORT,
    (BranchType.DEV, BranchType.FEATURE): CommitType.CATCH_UP,
    (BranchType.HOTFIX, BranchType.MAIN): CommitType.HOTFIX_RELEASE,
    (BranchType.HOTFIX, BranchType.DEV): CommitType.HOTFIX_BACKPORT,
    (BranchType.RELEASE, BranchType.MAIN): CommitType.RELEASE_CUT,
    (BranchType.RELEASE, BranchType.DEV): CommitType.RELEASE_BACKPORT,
}
