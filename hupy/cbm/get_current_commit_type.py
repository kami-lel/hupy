"""
get_current_commit_type.py

identify the type of an in-progress git commit
"""

# Todo expose commit type in CLI

import os

from hupy.kamilog import getLogger
from hupy.cbm import CBM_LOGGER_NAME
from hupy.cbm.branch_type import BranchType
from hupy.cbm.commit_type import CommitType
from hupy.config_file.load_config import load_hupy_config

__all__ = ("get_current_commit_type", "get_source_branch", "get_target_branch")

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


# pylint: disable-next=invalid-name
_source_branch_cache = {}
# pylint: disable-next=invalid-name
_target_branch_cache = {}
# pylint: disable-next=invalid-name
_commit_type_cache = {}


# Public API  ##################################################################


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


def get_target_branch(repo):
    """
    get the target branch name of the current merge, (result is cached)


    :param repo: git repository object
    :type repo: git.Repo
    :return: name of the target branch being merged into, or ``None``
                    on a detached HEAD
    :rtype: str or None
    """
    if repo.git_dir in _target_branch_cache:
        return _target_branch_cache[repo.git_dir]

    try:
        _target_branch_cache[repo.git_dir] = repo.active_branch.name
    except TypeError:
        _target_branch_cache[repo.git_dir] = None  # detached HEAD
    return _target_branch_cache[repo.git_dir]


def get_current_commit_type(repo):
    """
    return the type of the current in-progress commit, (result is cached)


    :param repo: git repository object
    :type repo: git.Repo
    :return: a public member of ``CommitType``
    :rtype: CommitType
    :example:
    >>> get_current_commit_type(repo)
    <CommitType.REGULAR_COMMIT: ...>
    """
    if repo.git_dir in _commit_type_cache:
        return _commit_type_cache[repo.git_dir]

    gd = repo.git_dir

    if not _has_state(gd, "MERGE_HEAD"):
        logger.debug("detect regular commit")
        _commit_type_cache[repo.git_dir] = CommitType.REGULAR_COMMIT
        return _commit_type_cache[repo.git_dir]

    lines = _read_merge_head(gd)
    if len(lines) != 1:  # octopus merge
        logger.debug("detect octopus merge")
        _commit_type_cache[repo.git_dir] = CommitType.OTHER_MERGE
        return _commit_type_cache[repo.git_dir]

    sha = lines[0]
    target = get_target_branch(repo)

    if _is_pull_merge(repo, sha, target):
        logger.debug("detect pull merge")
        _commit_type_cache[repo.git_dir] = CommitType.OTHER_MERGE
        return _commit_type_cache[repo.git_dir]

    cbm_config = load_hupy_config(repo).cbm

    source = get_source_branch(repo)
    source_type = BranchType.from_name(source, cbm_config)
    target_type = (
        None if target is None else BranchType.from_name(target, cbm_config)
    )

    commit_type = CommitType.decide_commit_type(source_type, target_type)
    logger.debug("detect {} merge".format(commit_type.name))
    _commit_type_cache[repo.git_dir] = commit_type
    return _commit_type_cache[repo.git_dir]
