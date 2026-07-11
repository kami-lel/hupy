"""
ver_grep.py
"""

import git

from hupy.should_run_module import should_run_module
from hupy.kamilog import getLogger
from hupy.config_file.load_config import load_hupy_config

from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# auxiliaries  ##################################################################
def _read_version_file_at_ref(repo, ref, version_file):
    """
    :return: the file's content at ref; or ``None`` when absent
    """
    try:
        return repo.git.show("{}:{}".format(ref, version_file.as_posix()))
    except git.GitCommandError:
        logger.warning(
            "version file not found on {}: {}".format(ref, version_file)
        )
        return None


# Public API  ##################################################################


def grep_version(repo, state_file, ref):
    if should_run_module(repo, state_file, "vg"):
        return ""

    # get version file path & pattern  -----------------------------------------
    config = load_hupy_config(repo)

    version_file = config.vg.version_file
    logger.debug("version_file:\t{}".format(version_file))
    pattern = config.vg.version_line_pattern
    logger.debug("version_line_pattern:\t{}".format(pattern))

    if str(version_file) in ("", ".") or not pattern.strip():
        logger.warning("unconfigured")  # TODO better word
        return ""

    pass  # TODO TODO
