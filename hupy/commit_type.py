"""
commit_type.py

identify the type of an in-progress git commit
"""

import os
from enum import Flag, auto

import git

# helpers  #####################################################################


class CommitType(Flag):  # =====================================================
    """
    represent the type of an in-progress git commit with two-level
    hierarchy: level 1 distinguishes merges from other commits;
    level 2 further categorizes merges by strategy
    """

    _OTHER_COMMIT = auto()
    _FEATURE_FINISH = auto()
    _VERSION_RELEASE = auto()
    _OTHER_MERGE = auto()
    _CHERRY_PICK = auto()
    _REVERT = auto()
    _INITIAL = auto()
    _REGULAR = auto()

    # Public Member  -----------------------------------------------------------

    MERGE = auto()
    OTHER_COMMIT = _OTHER_COMMIT

    FEATURE_FINISH = MERGE | _FEATURE_FINISH
    VERSION_RELEASE = MERGE | _VERSION_RELEASE
    OTHER_MERGE = MERGE | _OTHER_MERGE


def _has_state(git_dir, name):
    return os.path.isfile(os.path.join(git_dir, name))


# Public API ###################################################################
def get_current_commit_type(repo_path="."):
    """
    return the type of the current in-progress commit


    :param repo_path: path to the git repository or any of its
            subdirectories; defaults to the current directory
    :type repo_path: str
    :raises git.InvalidGitRepositoryError: if no git repository is
            found at or above ``repo_path``
    :raises git.NoSuchPathError: if ``repo_path`` does not exist
    :return: a public member of ``CommitType``
    :rtype: CommitType
    :example:
    >>> get_current_commit_type()
    <CommitType.OTHER_COMMIT: ...>
    """
    repo = git.Repo(repo_path, search_parent_directories=True)
    gd = repo.git_dir
    if _has_state(gd, "MERGE_HEAD"):
        return CommitType.OTHER_MERGE  # FIXME implement actual logic

    # BUG it fail to understand remote branch pull
    return CommitType.OTHER_COMMIT
