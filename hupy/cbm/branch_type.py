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
    def from_name(cls, branch_name, cbm_config):
        """
        :param branch_name: name of the git branch to classify
        :type branch_name: str
        :param cbm_config: the loaded ``cbm`` config section
        :type cbm_config: hupy.config.config_file._Cbm
        :return: the branch type matching ``branch_name``
        :rtype: BranchType
        """
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
