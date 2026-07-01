"""
tt_detect.py

triage tag detection and flag enum with instances, groups, and
search utilities for finding tags in lines and staged git diffs
"""

import re
import subprocess
from enum import Flag, auto

# constants  ###################################################################

_TT_PATTERN = (
    r"\b(TODO|FIXME|HACK|BUG|Todo|Fixme|Hack|Bug|" r"todo|fixme|hack|bug)\b"
)

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
    def filter_by_group(cls, tags, group):
        """
        filter tags by group membership.

        return only tags that belong to the specified group
        (e.g. ``LOUDS``, ``FIXMES``, ``TODOS | STEADYS``).


        :param tags: ``TriageTagType`` members to filter
        :type tags: iterable
        :param group: ``TriageTagType`` group to filter by
        :type group: TriageTagType
        :return: tags that belong to the group
        :rtype: list
        """
        return [tag for tag in tags if tag in group]

    @classmethod
    def find_first_in_line(cls, line):
        """
        find first triage tag in a line.

        scan a line for the first occurrence of a triage tag and
        return the corresponding ``TriageTagType`` member.


        :param line: line of text to scan
        :type line: str
        :return: the first ``TriageTagType`` member found, or ``None``
        :rtype: TriageTagType or None
        """
        match = re.search(_TT_PATTERN, line)
        if not match:
            return None

        tag_text = match.group(1)
        member_name = _TT_STR_TO_NAME[tag_text]
        return getattr(cls, member_name)


# Public API  ##################################################################


# todo detect TT with respect of code comment by file type


def detect_triage_tags_in_staged_file(file_path, repo_root=None):
    """
    detect triage tags in staged additions.

    scan git staged diff for added lines containing triage tags
    (TODO, FIXME, HACK, BUG) in all three tiers (Loud, Steady,
    Quiet).


    :param file_path: path to the file to scan, relative to
            ``repo_root`` when given
    :type file_path: str
    :param repo_root: path to the git repository or any of its
            subdirectories; defaults to the current directory
    :type repo_root: str or None
    :return: list of tuples ``(tag_member, line)`` for detected tags
    :rtype: list
    """
    try:
        diff_output = subprocess.check_output(
            ("git", "diff", "--cached", "--", file_path),
            text=True,
            stderr=subprocess.PIPE,
            cwd=repo_root,
        )
    except subprocess.CalledProcessError:
        return []

    results = []

    for line in diff_output.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added_line = line[1:]
            tag_member = TriageTagType.find_first_in_line(added_line)
            if tag_member:
                results.append((tag_member, added_line))

    return results
