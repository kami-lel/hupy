"""
gcv.py

extract a repo's version string by regex-matching a line in a
configured version file
"""

import os
import re

from hupy.config.load_config import load_hupy_config
from hupy.kamilog import getLogger
from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################
def _load_ver_grep_settings():
    """
    load the ``ver_grep`` section of the HUPy config for the current
    working directory
    """
    config = load_hupy_config(os.getcwd())

    if config.ver_grep.is_unconfigured():
        return None

    version_file = config.ver_grep.version_file
    logger.debug("version_file:\t{}".format(version_file))
    pattern = config.ver_grep.version_line_pattern
    logger.debug("version_line_pattern:\t{}".format(pattern))
    return version_file, pattern


def _grep_version_from_content(
    content, version_file, pattern, branch_label="current branch"
):
    """
    regex-match ``pattern`` line by line against ``content``, returning
    the first capturing group of the first matching line

    :param branch_label: human-readable source of ``content``, used to
            disambiguate log output, eg ``"current branch"`` or
            ``"source branch"``
    :type branch_label: str
    """
    for line in content.splitlines():
        match = re.search(pattern, line)
        if match:
            logger.debug(
                "matched line on {}:\n{}".format(branch_label, line)
            )
            version = match.group(1)
            logger.debug(
                "version grepped on {}:\t{}".format(branch_label, version)
            )
            return version

    logger.error(
        "no line matches pattern in {} on {}: {}".format(
            version_file, branch_label, pattern
        )
    )
    raise SystemExit(1)


# Public API  ##################################################################
def grep_current_version():
    """
    extract version string from the repository's version file using
    the configured regex pattern; the pattern must contain a capturing
    group whose content is returned.


    :raises SystemExit: version file not found or pattern does not
            match any line
    :return: the captured group from the first matching line, or
            ``""`` if ver_grep is not configured
    :rtype: str
    """
    settings = _load_ver_grep_settings()
    if settings is None:
        return ""
    version_file, pattern = settings

    if not version_file.exists():
        logger.error("version file not found: {}".format(version_file))
        raise SystemExit(1)

    content = version_file.read_text()

    return _grep_version_from_content(content, version_file, pattern)
