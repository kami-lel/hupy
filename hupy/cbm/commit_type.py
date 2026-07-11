"""
commit_type.py

commit type flag: categorize git commits by merge strategy
"""

from enum import Flag, auto

from hupy.cbm.branch_type import BranchType

__all__ = ("CommitType",)


class CommitType(Flag):  #######################################################
    """
    represent the type of an in-progress git commit with two-level
    hierarchy: level 2 gives each merge subtype its own bit, level 1
    exposes ``MERGE`` as the union of every merge subtype so a single
    bit test can categorize both a specific subtype and any merge.

    See `docs/cbm_doc.md` for detailed descriptions of each merge type.
    """

    # Member  ------------------------------------------------------------------

    # non-merge commits
    REGULAR_COMMIT = auto()
    OTHER_COMMIT = auto()

    # merge
    FEATURE_LANDING = auto()
    VERSION_RELEASE = auto()
    SYNC_BACKPORT = auto()
    CATCH_UP = auto()
    HOTFIX_RELEASE = auto()
    HOTFIX_BACKPORT = auto()
    RELEASE_CUT = auto()
    RELEASE_BACKPORT = auto()
    OTHER_MERGE = auto()

    # merge categories
    # release = merge into main
    RELEASE = VERSION_RELEASE | HOTFIX_RELEASE | RELEASE_CUT
    BACKPORT = SYNC_BACKPORT | HOTFIX_BACKPORT | RELEASE_BACKPORT
    INTEGRATION = RELEASE | FEATURE_LANDING
    # all merges
    MERGE = INTEGRATION | BACKPORT | CATCH_UP | OTHER_MERGE

    # Public Method  -----------------------------------------------------------

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
