"""
changed_files.py

resolve the set of file paths changed by the current hook
invocation, per hook: staged files for ``pre-commit`` and
``pre-merge-commit``, the about-to-be-replayed range for
``pre-rebase``
"""

import git

from hupy.pt import PT_LOGGER_NAME
from hupy.kamilog import getLogger

# logger  ######################################################################
logger = getLogger(PT_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


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


def _get_rebase_range_file_paths(repo, hooks_args):
    """
    :param hooks_args: raw ``pre-rebase`` hook arguments: upstream,
            then the branch being rebased (empty when rebasing the
            current branch)
    :type hooks_args: collections.abc.Sequence[str]
    :return: paths of files changed between ``upstream`` and
            ``branch``
    :rtype: list[str]
    """
    if not hooks_args:
        logger.warning("pre-rebase hook args missing upstream")
        return []

    upstream = hooks_args[0]
    branch = hooks_args[1] if len(hooks_args) > 1 and hooks_args[1] else "HEAD"

    try:
        output = repo.git.diff(
            "--name-only", "{}...{}".format(upstream, branch)
        )
    except git.GitCommandError as e:
        logger.critical("unable to get git rebase range files")
        raise SystemExit(1) from e

    return [file_path for file_path in output.splitlines() if file_path]


# Public API  ##################################################################


def get_changed_file_paths(repo, hook_name, hooks_args=()):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :param hook_name: hook name, eg ``"pre-commit"``
    :type hook_name: str
    :param hooks_args: raw arguments forwarded by the git hook invocation
    :type hooks_args: collections.abc.Sequence[str], optional
    :return: paths of files changed by this hook invocation
    :rtype: list[str]
    """
    if hook_name == "pre-rebase":
        return _get_rebase_range_file_paths(repo, hooks_args)

    return _get_staged_file_paths(repo)
