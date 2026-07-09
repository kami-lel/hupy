"""
dvut.py

decide which part of the version core (major/minor/patch) a coming
version bumps relative to the current version
"""

import re

from hupy.kamilog import getLogger
from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False

VERSION_CORE_PATTERN = r"^(\d+)\.(\d+)\.(\d+)"


# helpers  #####################################################################
def _parse_version_core(version):
    """
    parse a version string's ``major.minor.patch`` core into ints,
    ignoring any pre-release or build metadata suffix
    """
    match = re.match(VERSION_CORE_PATTERN, version)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


# Public API  ##################################################################
def decide_version_update_type(coming_version, current_version):
    """
    decide which version-core component ``coming_version`` bumps
    relative to ``current_version``


    :param coming_version: candidate version string to compare
    :type coming_version: str
    :param current_version: version string currently in effect
    :type current_version: str
    :return: ``"x"`` for a major update, ``"y"`` for a minor update,
            ``"z"`` for a patch update, or ``""`` when either version
            core cannot be parsed, or ``coming_version`` is not an
            update over ``current_version``
    :rtype: str
    """
    coming_core = _parse_version_core(coming_version)
    current_core = _parse_version_core(current_version)
    if coming_core is None or current_core is None:
        return ""

    coming_major, coming_minor, coming_patch = coming_core
    current_major, current_minor, current_patch = current_core

    if coming_major > current_major:
        return "x"
    if coming_major == current_major and coming_minor > current_minor:
        return "y"
    if (
        coming_major == current_major
        and coming_minor == current_minor
        and coming_patch > current_patch
    ):
        return "z"

    return ""
