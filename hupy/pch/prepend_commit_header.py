"""
prepend_commit_header.py

prepend commit type header to commit message
"""

import os
import re
import tempfile

from hupy.config_file.load_config import load_hupy_config
from hupy.kamilog import getLogger
from hupy.should_run_module import should_run_module
from hupy.ver_grep import (
    decide_version_update_type,
    grep_source_branch_version,
    grep_target_branch_version,
)
from . import PCH_LOGGER_NAME
from hupy.cbm import CommitType
from hupy.cbm.get_current_commit_type import (
    get_current_commit_type,
    get_source_branch,
    get_target_branch,
)

# logger  ######################################################################
logger = getLogger(PCH_LOGGER_NAME)
logger.propagate = False


# auxiliary  ###################################################################


def _get_version_bump_prefix(source_version, target_version):
    """
    map a source/target version comparison to a header word prefix
    """
    bump_type = decide_version_update_type(source_version, target_version)
    if bump_type == "x":
        return "Major "
    elif bump_type == "y":
        return "Minor "
    elif bump_type == "z":
        return "Patch "
    else:
        return ""


def _get_release_type_word(version, repo):
    """
    map a version string to its release-type word
    """
    pch_config = load_hupy_config(repo).pch
    tagged_words = (
        (pch_config.alpha_tag, "Alpha Release "),
        (pch_config.beta_tag, "Beta Release "),
        (pch_config.release_candidate_tag, "Release Candidate "),
    )
    for tag, word in tagged_words:
        if tag and tag in version:
            return word

    if pch_config.enable_pre_alpha and re.match(r"^0\.9\.\d+", version):
        return "Pre-Alpha Release "
    if pch_config.enable_vertical_slice and re.match(
        r"^0\.[5-9]\.\d+", version
    ):
        return "Vertical Slice Release "
    if re.match(r"^0\.\d+\.\d+", version):
        return "Prototype Release "
    if re.match(r"^\d+\.\d+\.\d+", version):
        return "Stable Release "
    return ""


def _gen_bumped_version_header(header_word):
    """
    build a "<header_word>: <version>" header, prefixed with the
    version's major/minor/patch bump word when a source version
    resolves
    """
    version = grep_source_branch_version()
    if version:
        prefix = _get_version_bump_prefix(version, grep_target_branch_version())
        return "{}{}: {}".format(prefix, header_word, version)
    else:
        return header_word


def _gen_backport_header(header_word):
    """
    build a "<header_word> from: <version>" header, or plain
    ``header_word`` when no source version resolves
    """
    version = grep_source_branch_version()
    if version:
        return "{} from: {}".format(header_word, version)
    else:
        return header_word


# generate header  =============================================================


def _gen_version_release_header(repo):
    version = grep_source_branch_version()
    if not version:
        return "Version Release"

    release_type = _get_release_type_word(version, repo)
    if not release_type:
        return "Version Release: {}".format(version)

    if release_type in (
        "Alpha Release ",
        "Beta Release ",
        "Release Candidate ",
    ):
        bump_prefix = ""
    else:
        bump_prefix = _get_version_bump_prefix(
            version, grep_target_branch_version()
        )

    return "{}: {}".format((bump_prefix + release_type).rstrip(), version)


def _gen_feature_landing_header(repo):
    branch_name = get_source_branch(repo)
    return "Feature Landing: {}".format(branch_name)


def _gen_sync_backport_header(_):
    return _gen_backport_header("Sync Backport")


def _gen_catch_up_header(repo):
    branch_name = get_target_branch(repo)
    return "Catch Up: {}".format(branch_name)


def _gen_hotfix_release_header(_):
    return _gen_bumped_version_header("Hotfix Release")


def _gen_hotfix_backport_header(_):
    return _gen_backport_header("Hotfix Backport")


def _gen_release_cut_header(_):
    return _gen_bumped_version_header("Release Cut")


def _gen_release_backport_header(_):
    return _gen_backport_header("Release Backport")


_HEADER_GENERATORS = {
    CommitType.VERSION_RELEASE: _gen_version_release_header,
    CommitType.FEATURE_LANDING: _gen_feature_landing_header,
    CommitType.SYNC_BACKPORT: _gen_sync_backport_header,
    CommitType.CATCH_UP: _gen_catch_up_header,
    CommitType.HOTFIX_RELEASE: _gen_hotfix_release_header,
    CommitType.HOTFIX_BACKPORT: _gen_hotfix_backport_header,
    CommitType.RELEASE_CUT: _gen_release_cut_header,
    CommitType.RELEASE_BACKPORT: _gen_release_backport_header,
}


# Public API  ##################################################################
def prepend_commit_header(repo, state_file):
    """
    prepend commit type header to the current commit message.


    :param repo: git repository object
    :type repo: git.Repo
    :param state_file: the open HUPy state file, as yielded by
            ``open_state_file``
    :type state_file: HupyStateFile
    """
    if not should_run_module(repo, state_file, "pch"):
        return

    logger.enter("perform Prepend Commit Header")

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
