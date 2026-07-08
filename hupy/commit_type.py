"""
commit_type.py

identify the type of an in-progress git commit
"""

# todo consider expose commit type as part of cli

import os
from enum import Flag, auto

import git

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import getLogger

# logger  ######################################################################
logger = getLogger(PROJ_LOGGER_NAME + ".commit_type")
logger.propagate = False


# constants  ###################################################################

# todo make branch names configurable
MAIN_BRANCH = "main"
DEV_BRANCH = "dev"


class CommitType(Flag):  #######################################################
    """
    represent the type of an in-progress git commit with two-level
    hierarchy: level 1 distinguishes merges from other commits;
    level 2 further categorizes merges by strategy
    """

    _FEATURE_FINISH = auto()
    _VERSION_RELEASE = auto()
    _OTHER_MERGE = auto()

    # Public Member  -----------------------------------------------------------

    MERGE = auto()
    OTHER_COMMIT = auto()

    FEATURE_FINISH = MERGE | _FEATURE_FINISH
    VERSION_RELEASE = MERGE | _VERSION_RELEASE
    OTHER_MERGE = MERGE | _OTHER_MERGE


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

# todo save values to cached, which is reset per commit


def get_source_branch(repo):
    """
    get the source branch name of the current merge


    :param repo: git repository object
    :type repo: git.Repo
    :return: name of the source branch being merged
    :rtype: str
    """
    merge_head_path = os.path.join(repo.git_dir, "MERGE_HEAD")
    with open(merge_head_path, encoding="utf-8") as f:
        sha = f.read().strip()
    for branch in repo.branches:
        if branch.commit.hexsha == sha:
            return branch.name
    return repo.git.name_rev("--name-only", sha)


def get_current_commit_type(repo_path):
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
    >>> get_current_commit_type(repo_path)
    <CommitType.OTHER_COMMIT: ...>
    """
    repo = git.Repo(repo_path, search_parent_directories=True)
    gd = repo.git_dir

    if not _has_state(gd, "MERGE_HEAD"):
        logger.debug("detect regular commit")
        return CommitType.OTHER_COMMIT

    lines = _read_merge_head(gd)
    if len(lines) != 1:  # octopus merge
        logger.debug("detect octopus merge")
        return CommitType.OTHER_MERGE

    sha = lines[0]
    target = _get_target_branch(repo)

    if _is_pull_merge(repo, sha, target):
        logger.debug("detect pull merge")
        return CommitType.OTHER_MERGE

    source = get_source_branch(repo)

    if source != MAIN_BRANCH and target == DEV_BRANCH:
        logger.debug("detect Feature Finish merge")
        return CommitType.FEATURE_FINISH
    if source == DEV_BRANCH and target == MAIN_BRANCH:
        logger.debug("detect Version Release merge")
        return CommitType.VERSION_RELEASE

    logger.debug("detect regular merge")
    return CommitType.OTHER_MERGE
