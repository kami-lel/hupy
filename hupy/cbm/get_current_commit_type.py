"""
get_current_commit_type.py

identify the type of an in-progress git commit
"""

# todo consider expose commit type as part of cli

import os

import git

from hupy.kamilog import getLogger
from hupy.cbm.commit_type import (
    CommitType,
    MAIN_BRANCH,
    DEV_BRANCH,
    CBM_LOGGER_NAME,
)

__all__ = ("get_current_commit_type", "get_source_branch")

# logger  ######################################################################

logger = getLogger(CBM_LOGGER_NAME)
logger.propagate = False


# helper functions  ############################################################


def _has_state(git_dir, name):
    return os.path.isfile(os.path.join(git_dir, name))


def _read_merge_head(git_dir):
    path = os.path.join(git_dir, "MERGE_HEAD")
    # pylint: disable-next=unspecified-encoding
    with open(path) as f:
        return [ln.strip() for ln in f if ln.strip()]


def _get_target_branch(repo):
    try:
        return repo.active_branch.name
    except TypeError:
        return None  # detached HEAD


def _is_pull_merge(repo, sha, target_branch):
    if target_branch is None:
        return False
    for remote in repo.remotes:
        try:
            ref = remote.refs[target_branch]
            if ref.commit.hexsha == sha:
                return True
        except IndexError:
            continue
    return False


# Public API  ##################################################################

# pylint: disable-next=invalid-name
_source_branch_cache = {}
# pylint: disable-next=invalid-name
_commit_type_cache = {}


def get_source_branch(repo):
    """
    get the source branch name of the current merge, (result is cached)


    :param repo: git repository object
    :type repo: git.Repo
    :return: name of the source branch being merged
    :rtype: str
    """
    if repo.git_dir in _source_branch_cache:
        return _source_branch_cache[repo.git_dir]

    merge_head_path = os.path.join(repo.git_dir, "MERGE_HEAD")
    with open(merge_head_path, encoding="utf-8") as f:
        sha = f.read().strip()
    for branch in repo.branches:
        if branch.commit.hexsha == sha:
            _source_branch_cache[repo.git_dir] = branch.name
            return _source_branch_cache[repo.git_dir]
    _source_branch_cache[repo.git_dir] = repo.git.name_rev("--name-only", sha)
    return _source_branch_cache[repo.git_dir]


def get_current_commit_type(repo_path):
    """
    return the type of the current in-progress commit, (result is cached)


    :param repo_path: path to the git repository or any of its
                    subdirectories; defaults to the current directory
    :type repo_path: str
    :raises git.InvalidGitRepositoryError: if no git repository is
                    found at or above ``repo_path``
    :raises git.NoSuchPathError: if ``repo_path`` does not exist
    :return: a public member of ``CommitType``
    :rtype: CommitType
    :example:
    >>> get_current_commit_type(repo_path)
    <CommitType.OTHER_COMMIT: ...>
    """
    if repo_path in _commit_type_cache:
        return _commit_type_cache[repo_path]

    repo = git.Repo(repo_path, search_parent_directories=True)
    gd = repo.git_dir

    if not _has_state(gd, "MERGE_HEAD"):
        logger.debug("detect regular commit")
        _commit_type_cache[repo_path] = CommitType.OTHER_COMMIT
        return _commit_type_cache[repo_path]

    lines = _read_merge_head(gd)
    if len(lines) != 1:  # octopus merge
        logger.debug("detect octopus merge")
        _commit_type_cache[repo_path] = CommitType.OTHER_MERGE
        return _commit_type_cache[repo_path]

    sha = lines[0]
    target = _get_target_branch(repo)

    if _is_pull_merge(repo, sha, target):
        logger.debug("detect pull merge")
        _commit_type_cache[repo_path] = CommitType.OTHER_MERGE
        return _commit_type_cache[repo_path]

    source = get_source_branch(repo)

    if source != MAIN_BRANCH and target == DEV_BRANCH:
        logger.debug("detect Feature Landing merge")
        _commit_type_cache[repo_path] = CommitType.FEATURE_LANDING
        return _commit_type_cache[repo_path]
    if source == DEV_BRANCH and target == MAIN_BRANCH:
        logger.debug("detect Version Release merge")
        _commit_type_cache[repo_path] = CommitType.VERSION_RELEASE
        return _commit_type_cache[repo_path]

    logger.debug("detect regular merge")
    _commit_type_cache[repo_path] = CommitType.OTHER_MERGE
    return _commit_type_cache[repo_path]
