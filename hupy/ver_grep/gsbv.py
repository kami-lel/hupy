"""
gsbv.py

extract the version string of an in-progress merge's source (incoming)
branch, by regex-matching a line in its configured version file; read
straight from the source branch tip via git, since the working tree
mid-merge holds the (possibly conflicted) target branch content
"""

import os

import git

from hupy.cbm import get_source_branch
from hupy.kamilog import getLogger
from . import VER_GREP_LOGGER_NAME
from .gcv import _grep_version_from_content, _load_ver_grep_settings

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################
def _read_version_file_at_ref(repo, ref, version_file):
    """
    read version_file's content as it exists at ref
    """
    try:
        return repo.git.show("{}:{}".format(ref, version_file.as_posix()))
    except git.GitCommandError as e:
        logger.error(
            "version file not found on {}: {}".format(ref, version_file)
        )
        raise SystemExit(1) from e


# Public API  ##################################################################
def grep_source_branch_version():
    """
    extract version string from the source (incoming) branch's version
    file, using the configured regex pattern; the pattern must contain
    a capturing group whose content is returned.


    :raises SystemExit: version file not found on the source branch,
            or the pattern does not match any line
    :return: the captured group from the first matching line, or
            ``""`` if ver_grep is not configured
    :rtype: str
    """
    settings = _load_ver_grep_settings()
    if settings is None:
        return ""
    version_file, pattern = settings

    # TODO TODO logger

    repo = git.Repo(os.getcwd(), search_parent_directories=True)
    source_branch = get_source_branch(repo)

    content = _read_version_file_at_ref(repo, source_branch, version_file)

    return _grep_version_from_content(content, version_file, pattern)
