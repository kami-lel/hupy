"""
ver_grep.py
"""

import pathlib
import re
import sys

import git

from hupy.should_run_module import should_run_module
from hupy.kamilog import AnsiRenderer, AnsiStyle, getLogger
from hupy.config_file.load_config import load_hupy_config

from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False
renderer = AnsiRenderer(sys.stdout)

# constants  ###################################################################

# sentinel `ref` value meaning "the local worktree file on disk", not
# a git ref
WORKTREE = None


# auxiliaries  #################################################################


def _read_occurrence_file(repo, ref, occurrence):
    """
    read a single configured occurrence's file content, either off the
    local worktree (when ``ref is WORKTREE``) or from the git object
    database at ``ref``
    """
    if ref is WORKTREE:
        path = pathlib.Path(repo.working_tree_dir) / occurrence.file
        try:
            return path.read_text()
        except FileNotFoundError:
            logger.warning(
                "missing file in worktree: {}".format(occurrence.file)
            )
            return ""

    try:
        return repo.git.show("{}:{}".format(ref, occurrence.file.as_posix()))
    except git.GitCommandError:
        logger.warning("missing file on {}: {}".format(ref, occurrence.file))
        return ""


def grep_occurrence(repo, ref, occurrence):
    """
    grep the version string out of a single configured occurrence's
    file, at a given git ref


    :param repo: git repository to read the file from
    :type repo: git.Repo
    :param ref: git ref to read the file at, or ``WORKTREE`` to read
            the on-disk worktree file instead
    :type ref: str or None
    :param occurrence: a single configured version occurrence
    :type occurrence: _VersionOccurrence
    :return: the captured version; or
            "" if the file is missing at ``ref``, no line matches
            ``occurrence.glob``, or the match lacks a capture group
            (each case is warned before returning)
    :rtype: str
    """
    content = _read_occurrence_file(repo, ref, occurrence)
    if not content:
        return ""

    for line in content.splitlines():
        match = re.search(occurrence.glob, line)
        if match:
            logger.debug("matched line on {}:\n{}".format(ref, line))
            if not match.groups():  # pattern lacks a capture group
                logger.warning(
                    "missing capture group in version pattern:\n{}".format(
                        occurrence.glob
                    )
                )
                return ""

            version = match.group(1)
            logger.debug("version grepped on {}:\t{!r}".format(ref, version))
            return version

    logger.warning(
        "version pattern line missing in file on {}: {}".format(
            ref, occurrence.file
        )
    )

    return ""


# Public API  ##################################################################
def grep_version(repo, state_file, ref):
    """
    grep the repo's canonical version string, from the first entry in
    ``vg.version_occurrences``, at a given git ref


    :param repo: git repository to read the version file from
    :type repo: git.Repo
    :param state_file:
    :type state_file: HupyStateFile
    :param ref: git ref to read the version file at, or ``WORKTREE``
            to read the on-disk worktree file instead
    :type ref: str or None
    :return: the grepped version; or
            "" if unconfigured, missing, or unmatched
    :rtype: str
    """

    if not should_run_module(repo, state_file, "vg"):
        return ""

    # get canonical occurrence  ------------------------------------------------
    config = load_hupy_config(repo)

    occurrences = config.vg.version_occurrences
    if not occurrences:
        logger.warning(
            "unconfigured:\nmust set {} to enable".format(
                renderer.color("version_occurrences", AnsiStyle.BOLD),
            )
        )
        return ""

    return grep_occurrence(repo, ref, occurrences[0])
