"""
prepend_commit_header.py

prepend commit type header to commit message
"""

import os
import tempfile

import git

from hupy.kamilog import getLogger
from . import PCH_LOGGER_NAME
from ..commit_type import (
    CommitType,
    get_current_commit_type,
    get_source_branch,
)

# logger  ######################################################################
logger = getLogger(PCH_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


def _gen_feature_finish_header_content(repo):
    """
    generate header content for Feature Finish commit type.
    """
    branch_name = get_source_branch(repo)
    return "Feature Finish: {}".format(branch_name)


def _gen_version_release_header_content():
    """
    generate header content for Version Release commit type.
    """
    return "Version Release"  # FIXME get version


def _prepend_commit_header_by_type(is_feature_finish, repo_root):
    """
    prepend a header line and a blank line to the commit message file.
    """
    repo = git.Repo(repo_root, search_parent_directories=True)
    commit_editmsg_path = os.path.join(repo.git_dir, "COMMIT_EDITMSG")

    content_lines = []
    comment_lines = []

    with open(commit_editmsg_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            target = (
                comment_lines
                if line.lstrip().startswith("#")
                else content_lines
            )
            target.append(line)

    if is_feature_finish:
        header = _gen_feature_finish_header_content(repo)
    else:
        header = _gen_version_release_header_content()

    logger.debug("generated header:\n" + header)

    content_lines = [header, ""] + content_lines

    directory = os.path.dirname(commit_editmsg_path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix="commit-msg.")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))
            f.write("\n")
            f.write("\n".join(comment_lines))
        os.replace(tmp_path, commit_editmsg_path)
    except BaseException:
        os.unlink(tmp_path)
        raise


# Public API  ##################################################################


def prepend_commit_header(repo_root):
    """
    prepend commit type header to the current commit message.


    :param repo_root: path to the git repository or any of its
            subdirectories
    :type repo_root: str
    """
    logger.enter("prepending commit header")

    commit_type = get_current_commit_type(repo_root)

    if CommitType.FEATURE_FINISH in commit_type:
        logger.debug("prepending header on Feature Finish merge")
        _prepend_commit_header_by_type(True, repo_root)

    elif CommitType.VERSION_RELEASE in commit_type:
        logger.debug("prepending header on Version Release merge")
        _prepend_commit_header_by_type(False, repo_root)

    else:
        logger.skip("regular commit/merge")
        return

    logger.pass_("commit header prepended")
