"""
prepend_commit_header.py

prepend commit type header to commit message
"""

import os
import tempfile

from hupy.kamilog import getLogger
from hupy.ver_grep import grep_source_branch_version
from . import PCH_LOGGER_NAME
from ..cbm import (
    CommitType,
    get_current_commit_type,
    get_source_branch,
)

# logger  ######################################################################
logger = getLogger(PCH_LOGGER_NAME)
logger.propagate = False


# auxiliary  ###################################################################


def _gen_version_release_header_content(_):
    # FIXME stable release & prototype & alpha/beta release w/ major/minor/patch
    version = grep_source_branch_version()
    if version:
        return "Version Release: {}".format(version)
    else:
        return "Version Release"


def _gen_feature_landing_header_content(repo):
    branch_name = get_source_branch(repo)
    return "Feature Landing: {}".format(branch_name)


def _gen_sync_backport_header(_):
    version = grep_source_branch_version()
    if version:
        return "Sync Backport from: {}".format(version)
    else:
        return "Sync Backport"


def _gen_catch_up_header(_):
    return "Catch Up"  # FIXME more word: eg target branch name


def _gen_hotfix_release_header(_):
    # FIXME w/ major/minor/patch
    version = grep_source_branch_version()
    if version:
        return "Hotfix Release: {}".format(version)
    else:
        return "Hotfix Release"


def _gen_hotfix_backport_header(_):
    version = grep_source_branch_version()
    if version:
        return "Hotfix Backport from: {}".format(version)
    else:
        return "Hotfix Backport"


def _gen_release_cut_header(_):
    # FIXME w/ major/minor/patch
    version = grep_source_branch_version()
    if version:
        return "Release Cut: {}".format(version)
    else:
        return "Release Cut"


def _gen_release_backport_header(_):
    version = grep_source_branch_version()
    if version:
        return "Release Backport from: {}".format(version)
    else:
        return "Release Backport"


_HEADER_GENERATORS = {
    CommitType.VERSION_RELEASE: _gen_version_release_header_content,
    CommitType.FEATURE_LANDING: _gen_feature_landing_header_content,
    CommitType.SYNC_BACKPORT: _gen_sync_backport_header,
    CommitType.CATCH_UP: _gen_catch_up_header,
    CommitType.HOTFIX_RELEASE: _gen_hotfix_release_header,
    CommitType.HOTFIX_BACKPORT: _gen_hotfix_backport_header,
    CommitType.RELEASE_CUT: _gen_release_cut_header,
    CommitType.RELEASE_BACKPORT: _gen_release_backport_header,
}


# Public API  ##################################################################
def prepend_commit_header(repo):
    """
    prepend commit type header to the current commit message.


    :param repo: git repository object
    :type repo: git.Repo
    """
    logger.enter("prepending commit header")

    commit_type = get_current_commit_type(repo)

    if commit_type not in _HEADER_GENERATORS:
        logger.skip("regular commit/merge")
        return

    logger.debug("prepending header on {} merge".format(commit_type.name))

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

    header = _HEADER_GENERATORS[commit_type](repo)

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

    logger.pass_("commit header prepended")
