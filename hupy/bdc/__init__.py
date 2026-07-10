"""
bdc package

ban direct commit — block commits made directly on protected branches
"""

from hupy import PROJ_LOGGER_NAME

BDC_LOGGER_NAME = PROJ_LOGGER_NAME + ".BDC"

from .ban_direct_commit import ban_direct_commit

__all__ = ("ban_direct_commit",)
