"""
branch_type.py

branch type flag: categorize git branches by naming convention
"""

from enum import Enum, auto

from hupy.config.load_config import load_hupy_config

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
    def from_name(cls, branch_name, repo_path):
        """
        :param branch_name: name of the git branch to classify
        :type branch_name: str
        :param repo_path: path to the repo root, or to any path inside
                    it; used to load the ``cbm`` config section
        :type repo_path: str
        :return: the branch type matching ``branch_name``
        :rtype: BranchType
        """
        cbm_config = load_hupy_config(repo_path).cbm

        if branch_name == cbm_config.dev_branch_name:
            return cls.DEV

        if branch_name == cbm_config.main_branch_name:
            return cls.MAIN

        if branch_name.startswith(cbm_config.hotfix_branch_prefix + "/"):
            return cls.HOTFIX

        if branch_name.startswith(cbm_config.release_branch_prefix + "/"):
            return cls.RELEASE

        if "/" in branch_name:
            return cls.USER

        return cls.FEATURE
