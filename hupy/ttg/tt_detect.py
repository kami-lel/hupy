"""
tt_detect.py

define ``TriageTag`` flag enum with triage tag instances and groups
"""

import re
import subprocess
from enum import Flag, auto

# constants  ###################################################################

_TT_STR_TO_NAME = {
    "TODO": "LOUD_TODO",
    "FIXME": "LOUD_FIXME",
    "HACK": "LOUD_HACK",
    "BUG": "LOUD_BUG",
    "Todo": "STEADY_TODO",
    "Fixme": "STEADY_FIXME",
    "Hack": "STEADY_HACK",
    "Bug": "STEADY_BUG",
    "todo": "QUIET_TODO",
    "fixme": "QUIET_FIXME",
    "hack": "QUIET_HACK",
    "bug": "QUIET_BUG",
}


# helpers  #####################################################################


class TriageTagType(Flag):  # ==================================================
    """
    triage tag flags organized in three tiers (Loud, Steady, Quiet).
    """

    # members  *****************************************************************

    # loud tier
    LOUD_TODO = auto()
    LOUD_FIXME = auto()
    LOUD_HACK = auto()
    LOUD_BUG = auto()

    # steady tier
    STEADY_TODO = auto()
    STEADY_FIXME = auto()
    STEADY_HACK = auto()
    STEADY_BUG = auto()

    # quiet tier
    QUIET_TODO = auto()
    QUIET_FIXME = auto()
    QUIET_HACK = auto()
    QUIET_BUG = auto()

    # groups by kind  ----------------------------------------------------------
    TODOS = LOUD_TODO | STEADY_TODO | QUIET_TODO
    FIXMES = LOUD_FIXME | STEADY_FIXME | QUIET_FIXME
    HACKS = LOUD_HACK | STEADY_HACK | QUIET_HACK
    BUGS = LOUD_BUG | STEADY_BUG | QUIET_BUG

    # groups by tier  ----------------------------------------------------------
    LOUDS = LOUD_TODO | LOUD_FIXME | LOUD_HACK | LOUD_BUG
    STEADYS = STEADY_TODO | STEADY_FIXME | STEADY_HACK | STEADY_BUG
    QUIETS = QUIET_TODO | QUIET_FIXME | QUIET_HACK | QUIET_BUG

    # Public Methods  **********************************************************

    @classmethod
    def from_str(cls, tag_str):
        """
        convert string to TriageTagType member.

        map string representations of triage tags (in any tier case)
        to the corresponding enum member.


        :param tag_str: triage tag as string (e.g. "TODO", "todo", "Todo")
        :type tag_str: str
        :return: the matching ``TriageTagType`` member
        :rtype: TriageTagType
        :raises ValueError: if ``tag_str`` is not a valid triage tag
        """
        if tag_str not in _TT_STR_TO_NAME:
            raise ValueError("invalid triage tag: {}".format(tag_str))

        member_name = _TT_STR_TO_NAME[tag_str]
        return getattr(cls, member_name)


# Public API  ##################################################################


def detect_triage_tags_in_staged_file(file_path):
    """
    detect triage tags in staged additions.

    scan git staged diff for added lines containing triage tags
    (TODO, FIXME, HACK, BUG) in all three tiers (Loud, Steady,
    Quiet).


    :param file_path: path to the file to scan
    :type file_path: str
    :return: list of tuples ``(tag_member, line)`` for detected tags
    :rtype: list
    """
    try:
        diff_output = subprocess.check_output(
            ("git", "diff", "--cached", "--", file_path),
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return []

    results = []
    tag_pattern = r"\b(TODO|FIXME|HACK|BUG|Todo|Fixme|Hack|Bug|todo|fixme|hack|bug)\b"  # noqa: E501

    for line in diff_output.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added_line = line[1:]
            for match in re.finditer(tag_pattern, added_line):
                tag_text = match.group(1)
                try:
                    tag_member = TriageTagType.from_str(tag_text)
                    results.append((tag_member, added_line))
                except ValueError:
                    pass

    return results
