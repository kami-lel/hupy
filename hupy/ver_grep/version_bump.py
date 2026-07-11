"""
version_bump.py

decide which part of the version core (major/minor/patch) a source
branch's version bumps relative to a target branch's version
"""

import re

from hupy.kamilog import getLogger
from . import VER_GREP_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(VER_GREP_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

VERSION_CORE_PATTERN = r"^(\d+)\.(\d+)\.(\d+)"


# auxiliary   ###################################################################
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
def decide_version_update_type(source_version, target_version):
    """
    decide which version-core component ``source_version`` bumps
    relative to ``target_version``


    :param source_version: candidate version string to compare, eg
            the source (incoming) branch's version
    :type source_version: str
    :param target_version: version string currently in effect, eg
            the target branch's version
    :type target_version: str
    :return: ``"x"`` for a major update, ``"y"`` for a minor update,
            ``"z"`` for a patch update, or ``""`` when either version
            core cannot be parsed, or ``source_version`` is not an
            update over ``target_version``
    :rtype: str
    """
    source_core = _parse_version_core(source_version)
    target_core = _parse_version_core(target_version)
    if source_core is None or target_core is None:
        return ""

    source_major, source_minor, source_patch = source_core
    target_major, target_minor, target_patch = target_core

    if source_major > target_major:
        return "x"
    if source_major == target_major and source_minor > target_minor:
        return "y"
    if (
        source_major == target_major
        and source_minor == target_minor
        and source_patch > target_patch
    ):
        return "z"

    return ""
