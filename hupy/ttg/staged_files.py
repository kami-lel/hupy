"""
staged_files.py

list staged files in a repo, filtered against ignored path globs
"""

import fnmatch
import subprocess

from hupy.ttg import TTG_LOGGER_NAME
from hupy.kamilog import getLogger

# logger  ######################################################################
logger = getLogger(TTG_LOGGER_NAME)


# Public API  ##################################################################


def is_path_ignored(file_path, ignored_path_globs):
    """
    :return: if ``file_path`` matches any glob in ``ignored_path_globs``
    :rtype: bool
    """
    return any(fnmatch.fnmatch(file_path, glob) for glob in ignored_path_globs)


def get_staged_file_paths(repo):
    """
    :return: paths of files staged in ``repo``
    :rtype: list
    """
    try:
        cached_files = (
            subprocess.check_output(
                ("git", "diff", "--cached", "--name-only"),
                text=True,
                stderr=subprocess.PIPE,
                cwd=repo.working_dir,
            )
            .strip()
            .split("\n")
        )
    except subprocess.CalledProcessError as e:
        logger.critical("unable to get git cached files")
        raise SystemExit(1) from e

    return [file_path for file_path in cached_files if file_path]
