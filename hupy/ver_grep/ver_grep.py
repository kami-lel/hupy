"""
ver_grep.py
"""

import re
import sys

import git

from hupy.should_run_module import should_run_module
from hupy.kamilog import AnsiRenderer, AnsiStyle, getLogger
from hupy.config_file.load_config import load_hupy_config

from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False
renderer = AnsiRenderer(sys.stdout)


# Public API  ##################################################################
def grep_version(repo, state_file, ref):
    """
    grep the version string from a version file at a given git ref


    :param repo: git repository to read the version file from
    :type repo: git.Repo
    :param state_file:
    :type state_file: HupyStateFile
    :param ref: git ref to read the version file at
    :type ref: str
    :return: the grepped version; or
            "" if unconfigured, missing, or unmatched
    :rtype: str
    """

    # FIXME verify & update general logger printed out
    if not should_run_module(repo, state_file, "vg"):
        return ""

    # get version file path & pattern  -----------------------------------------
    config = load_hupy_config(repo)

    version_file = config.vg.version_file
    logger.debug("version_file:\t{}".format(version_file))
    pattern = config.vg.version_line_pattern
    logger.debug("version_line_pattern:\t{}".format(pattern))

    if str(version_file) in ("", ".") or not pattern.strip():
        logger.warning(
            "unconfigured:\nmust set {}, {} to enable".format(
                renderer.color("version_file", AnsiStyle.BOLD),
                renderer.color("version_line_pattern", AnsiStyle.BOLD),
            )
        )
        return ""

    # load version file  -------------------------------------------------------
    try:
        content = repo.git.show("{}:{}".format(ref, version_file.as_posix()))
    except git.GitCommandError:
        logger.warning(
            "missing version file on {}: {}".format(ref, version_file)
        )
        return ""

    # grep version from content  -----------------------------------------------
    for line in content.splitlines():
        match = re.search(pattern, line)
        if match:
            logger.debug("matched line on {}:\n{}".format(ref, line))
            if not match.groups():  # pattern lacks a capture group
                logger.warning(
                    "pattern has no capture group on {}: {}".format(
                        ref, pattern
                    )
                )
                return ""

            version = match.group(1)
            logger.debug("version grepped on {}:\t{!r}".format(ref, version))
            return version

    logger.warning(
        "no line matches pattern in {} on {}: {}".format(
            version_file, ref, pattern
        )
    )

    return ""
