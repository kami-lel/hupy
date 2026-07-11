"""
branch_version.py

extract the version string of an in-progress merge's source (incoming)
or target (current) branch, by regex-matching a line in its configured
version file; read straight from each branch's own tip via git, since
the working tree mid-merge holds the (possibly conflicted) target
branch content
"""

import os
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


# helpers  #####################################################################
def _load_ver_grep_settings(repo):
    """
    load the ``vg`` section of the HUPy config for ``repo``

    :param repo: git repository object
    :type repo: git.Repo
    """
    config = load_hupy_config(repo)

    if config.vg.is_unconfigured():
        return None

    version_file = config.vg.version_file
    logger.debug("version_file:\t{}".format(version_file))
    pattern = config.vg.version_line_pattern
    logger.debug("version_line_pattern:\t{}".format(pattern))
    return version_file, pattern


def _grep_version_from_content(
    content, version_file, pattern, branch_label="current branch"
):
    """
    regex-match ``pattern`` line by line against ``content``, returning
    the first capturing group of the first matching line

    :param branch_label: human-readable source of ``content``, used to
            disambiguate log output, eg ``"source branch"`` or
            ``"target branch"``
    :type branch_label: str
    """
    for line in content.splitlines():
        match = re.search(pattern, line)
        if match:
            logger.debug(
                "matched line on {}:\n{}".format(branch_label, line)
            )
            if not match.groups():  # pattern lacks a capture group
                logger.warning(
                    "pattern has no capture group on {}: {}".format(
                        branch_label, pattern
                    )
                )
                return ""
            version = match.group(1)
            logger.debug(
                "version grepped on {}:\t{}".format(branch_label, version)
            )
            return version

    logger.warning(
        "no line matches pattern in {} on {}: {}".format(
            version_file, branch_label, pattern
        )
    )
    return ""


def _read_version_file_at_ref(repo, ref, version_file):
    """
    read version_file's content as it exists at ref, or ``None`` when
    the file is absent on that ref
    """
    try:
        return repo.git.show("{}:{}".format(ref, version_file.as_posix()))
    except git.GitCommandError:
        logger.warning(
            "version file not found on {}: {}".format(ref, version_file)
        )
        return None


# Public API  ##################################################################
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
