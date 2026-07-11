"""
branch_version.py

extract the version string of an in-progress merge's source (incoming)
or target (current) branch, by regex-matching a line in its configured
version file; read straight from each branch's own tip via git, since
the working tree mid-merge holds the (possibly conflicted) target
branch content
"""

import os
import pathlib
import re

import git

from hupy.cbm.get_current_commit_type import (
    get_source_branch,
    get_target_branch,
)
from hupy.config_file.load_config import load_hupy_config
from hupy.kamilog import getLogger
from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# Public API  ##################################################################
# FIXME refactor use new pattern
# TODO both take repo
def grep_source_branch_version():
    """
    extract version string from the source (incoming) branch's version
    file, using the configured regex pattern; the pattern must contain
    a capturing group whose content is returned.


    :return: the captured group from the first matching line, or ``""``
            when vg is disabled or unconfigured, the file is absent on
            the source branch, no line matches, or the pattern has no
            capture group
    :rtype: str
    """
    repo = git.Repo(os.getcwd(), search_parent_directories=True)
    settings = _load_ver_grep_settings(repo)
    if settings is None:
        return ""
    version_file, pattern = settings

    source_branch = get_source_branch(repo)

    content = _read_version_file_at_ref(repo, source_branch, version_file)
    if content is None:  # file absent on the source branch
        return ""

    return _grep_version_from_content(
        content, version_file, pattern, branch_label="source branch"
    )


def grep_target_branch_version():
    """
    extract version string from the target (current) branch's version
    file, using the configured regex pattern; the pattern must contain
    a capturing group whose content is returned.


    :return: the captured group from the first matching line, or ``""``
            when vg is disabled or unconfigured, the file is absent on
            the target branch, no line matches, or the pattern has no
            capture group
    :rtype: str
    """
    repo = git.Repo(os.getcwd(), search_parent_directories=True)
    settings = _load_ver_grep_settings(repo)
    if settings is None:
        return ""
    version_file, pattern = settings

    target_branch = get_target_branch(repo)

    content = _read_version_file_at_ref(repo, target_branch, version_file)
    if content is None:  # file absent on the target branch
        return ""

    return _grep_version_from_content(
        content, version_file, pattern, branch_label="target branch"
    )
