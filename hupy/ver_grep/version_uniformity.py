"""
version_uniformity.py

check that the repo's canonical version string (the first entry in
``vg.version_occurrences``) still appears, unchanged, in every other
configured occurrence
"""

import sys

from hupy.should_run_module import should_run_module
from hupy.kamilog import AnsiRenderer, AnsiStyle, getLogger
from hupy.config_file.load_config import load_hupy_config

from . import VER_GREP_LOGGER_NAME
from .ver_grep import grep_occurrence, grep_version

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False
_renderer = AnsiRenderer(sys.stdout)


# auxiliaries  #################################################################


def _heading(occurrence):
    """
    :param occurrence: a single configured version occurrence
    :type occurrence: _VersionOccurrence
    :return: ``occurrence.remark``, or the underlined file path
    :rtype: str
    """
    return occurrence.remark or _renderer.color(
        str(occurrence.file), AnsiStyle.UNDERLINE
    )


def _check_occurrence(repo, ref, canonical_version, occurrence):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :param ref: git ref to read the occurrence's file at
    :type ref: str
    :param canonical_version: the version grepped from the canonical
            occurrence
    :type canonical_version: str
    :param occurrence: a single configured version occurrence to check
    :type occurrence: _VersionOccurrence
    :return: ``None`` if uniform, else a failure message
    :rtype: str or None
    """
    heading = _heading(occurrence)
    found_version = grep_occurrence(repo, ref, occurrence)

    if not found_version:
        return "unreadable: {}".format(heading)

    if found_version != canonical_version:
        return "drifted: {}\nfound {!r}, expected {!r}".format(
            heading, found_version, canonical_version
        )

    logger.pass_("uniform: {}".format(heading))
    return None


# Public API  ##################################################################
def check_version_uniformity(repo, state_file, ref="HEAD", is_report_only=False):
    """
    assert every configured version occurrence beyond the canonical
    first entry still carries the same version; aborts the commit if
    any occurrence has drifted, unless ``is_report_only`` or
    ``vg.allow_version_uniformity_failure`` is set, in which case
    every failure only warns


    :param repo: git repository object
    :type repo: git.Repo
    :param state_file: the open HUPy state file, as yielded by
            ``open_state_file``
    :type state_file: HupyStateFile
    :param ref: git ref to check occurrences at; default="HEAD"
    :type ref: str, optional
    :param is_report_only: downgrade every failure to a warning
            instead of aborting; default=False
    :type is_report_only: bool, optional
    """
    if not should_run_module(repo, state_file, "vg"):
        return

    config = load_hupy_config(repo)

    if config.vg.disable_version_uniformity:
        logger.skip("Version Uniformity disabled in config file")
        return

    occurrences = config.vg.version_occurrences
    if len(occurrences) < 2:
        logger.skip("no occurrences configured beyond the canonical entry")
        return

    logger.enter("Version Uniformity")

    canonical_version = grep_version(repo, state_file, ref)
    if not canonical_version:
        return  # grep_version already warned

    failures = [
        message
        for occurrence in occurrences[1:]
        if (
            message := _check_occurrence(
                repo, ref, canonical_version, occurrence
            )
        )
        is not None
    ]

    if not failures:
        return

    is_soft = is_report_only or config.vg.allow_version_uniformity_failure
    for message in failures:
        if is_soft:
            logger.warning(message)
        else:
            logger.fail(message)

    if not is_soft:
        raise SystemExit(1)
