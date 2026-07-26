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


# Public API  ##################################################################
def check_version_uniformity(
    repo, state_file, ref="HEAD", is_report_only=False
):
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
        logger.skip("contains only canonical entry")
        return

    logger.enter("Version Uniformity")

    canonical_version = grep_version(repo, state_file, ref)
    if not canonical_version:
        return  # grep_version already warned

    is_soft = is_report_only or config.vg.allow_version_uniformity_failure
    failure_count = 0

    logger.debug("canonical version: {!r}".format(canonical_version))

    for occurrence in occurrences[1:]:
        heading = _heading(occurrence)
        found_version = grep_occurrence(repo, ref, occurrence)

        if not found_version:
            failure_count += 1
            message = "unreadable: {}".format(heading)
            if is_soft:
                logger.warning(message)
            else:
                logger.fail(message)
            continue

        if found_version != canonical_version:
            failure_count += 1
            message = (
                "version mismatched: {}\n(found: {} != canonical: {})".format(
                    heading, found_version, canonical_version
                )
            )
            if is_soft:
                logger.warning(message)
            else:
                logger.fail(message)
            continue

        logger.succ("version matched: {}".format(heading))

    if not failure_count:
        logger.pass_("Version Uniformity")
        return

    message = "{} occurrence(s) mismatched from canonical version".format(
        failure_count
    )
    if is_soft:
        logger.warning(message)
    else:
        logger.fail(message)
        raise SystemExit(1)
