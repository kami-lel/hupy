"""
branch_type.py

branch type flag: categorize git branches by naming convention
"""

from enum import Enum, auto

__all__ = ("BranchType",)


class BranchType(Enum):
    """
    represent the type of a git branch by its naming convention
    """

    FEATURE = auto()
    DEV = auto()
    MAIN = auto()
    HOTFIX = auto()
    RELEASE = auto()
    USER = auto()

    @classmethod
    def from_name(cls, branch_name):
        """
        :param branch_name: name of the git branch to classify
        :type branch_name: str
        :return: the branch type matching ``branch_name``
        :rtype: BranchType
        """
        # TODO make branch names configurable
        if branch_name == "dev":
            return cls.DEV

        if branch_name == "main":
            return cls.MAIN

        if branch_name.startswith("hotfix/"):
            return cls.HOTFIX

        if branch_name.startswith("release/"):
            return cls.RELEASE

        if "/" in branch_name:
            return cls.USER

        return cls.FEATURE
