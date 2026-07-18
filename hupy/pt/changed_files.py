"""
changed_files.py

resolve the set of file paths changed by the current hook
invocation: the staged files for ``pre-commit``,
``pre-merge-commit``, and ``pre-applypatch``
"""

import git

from hupy.pt import PT_LOGGER_NAME
from hupy.kamilog import getLogger

# logger  ######################################################################
logger = getLogger(PT_LOGGER_NAME)
logger.propagate = False


# auxiliaries  #################################################################


def _get_staged_file_paths(repo):
    """
    :return: paths of files staged in ``repo``
    :rtype: list[str]
    """
    try:
        output = repo.git.diff("--cached", "--name-only")
    except git.GitCommandError as e:
        logger.critical("unable to get git staged files")
        raise SystemExit(1) from e

    return [file_path for file_path in output.splitlines() if file_path]


# Public API  ##################################################################


def get_changed_file_paths(repo):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :return: paths of files changed by this hook invocation
    :rtype: list[str]
    """
    return _get_staged_file_paths(repo)
