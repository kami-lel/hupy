"""
pch package

prepend commit header — utilities for generating better commit messages
"""

from hupy import PROJ_LOGGER_NAME

PCH_LOGGER_NAME = PROJ_LOGGER_NAME + ".PCH"

from .prepend_commit_header import prepend_commit_header

__all__ = ("prepend_commit_header",)
