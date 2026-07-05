import os
import re

from hupy.config.load_config import load_hupy_config
from hupy.config.model import VER_GREP_LOGGER_NAME
from hupy.kamilog import getLogger

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# Public API  ##################################################################

# TODO warning fall back


def grep_repo_version():
    """
    extract version string from the repository's version file using
    the configured regex pattern; the pattern must contain a capturing
    group whose content is returned.


    :raises SystemExit: ver_grep is not configured (empty), version
            file not found, or pattern does not match any line
    :return: the captured group from the first matching line
    :rtype: str
    """
    config = load_hupy_config(os.getcwd())
    version_file = config.ver_grep.version_file
    pattern = config.ver_grep.version_line_pattern

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
