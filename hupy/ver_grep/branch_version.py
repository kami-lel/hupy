"""
branch_version.py

extract the version string of an in-progress merge's source (incoming)
or target (current) branch, by regex-matching a line in its configured
version file; read straight from each branch's own tip via git, since
the working tree mid-merge holds the (possibly conflicted) target
branch content
"""

from hupy.cbm.get_current_commit_type import (
    get_source_branch,
    get_target_branch,
)
from hupy.kamilog import getLogger
from . import VER_GREP_LOGGER_NAME
from .ver_grep import grep_version

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# TODO callers (prepend_commit_header.py) still use the old
# no-arg signature; thread repo/state_file through them
# Public API  ##################################################################
def grep_source_branch_version(repo, state_file):
    """
    grep the version string from the source (incoming) branch's version file


    :param repo:
    :type repo: git.Repo
    :param state_file:
    :type state_file: HupyStateFile
    :return: the grepped version; or
            "" if unconfigured, missing, or unmatched
    :rtype: str
    """
    return grep_version(repo, state_file, get_source_branch(repo))


def grep_target_branch_version(repo, state_file):
    """
    grep the version string from the target (current) branch's version file


    :param repo:
    :type repo: git.Repo
    :param state_file:
    :type state_file: HupyStateFile
    :return: the grepped version; or
            "" if unconfigured, missing, or unmatched
    :rtype: str
    """
    return grep_version(repo, state_file, get_target_branch(repo))
