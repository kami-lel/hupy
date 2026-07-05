"""
ver_grep.py

extract a repo's version string by regex-matching a line in a
configured version file
"""

import os
import re

from hupy import PROJ_LOGGER_NAME
from hupy.config.load_config import load_hupy_config
from hupy.kamilog import getLogger

# logger  ######################################################################

VER_GREP_LOGGER_NAME = PROJ_LOGGER_NAME + ".VerGrep"

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# Public API  ##################################################################
def grep_repo_version():
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
    config = load_hupy_config(os.getcwd())
    version_file = config.ver_grep.version_file
    pattern = config.ver_grep.version_line_pattern

    if str(version_file) in ("", ".") or not pattern.strip():
        logger.warning(
            "ver_grep is not configured:\n"
            "set version_file and version_line_pattern in HUPy config file"
        )
        return ""

    if not version_file.exists():
        logger.error("version file not found: {}".format(version_file))
        raise SystemExit(1)

    content = version_file.read_text()

    for line in content.splitlines():
        match = re.search(pattern, line)
        if match:
            return match.group(1)

    logger.error(
        "no line matches pattern in {}: {}".format(version_file, pattern)
    )
    raise SystemExit(1)
