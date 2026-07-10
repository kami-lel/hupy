"""
triage_tag_type.py

triage tag flag enum with tier/kind groups and search utilities
for finding tags in lines
"""

import re
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


# Public API  ##################################################################


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

    # HACK mv this away

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

    # HACK rf this to be its own

    @classmethod
    def find_first_in_line(cls, line, comment_prefix=None):
        """
        find first triage tag in a line.

        scan a line for the first occurrence of a triage tag and
        return the corresponding ``TriageTagType`` member. when
        ``comment_prefix`` is given, only a tag occurring after that
        comment-leader token on the line counts as a match; otherwise
        the tag is matched anywhere in the line.


        :param line: line of text to scan
        :type line: str
        :param comment_prefix: comment-leader token (eg ``"//"``,
                ``"#"``, ``"<!--"``) the tag must follow, or ``None``
                to match the tag anywhere in the line
        :type comment_prefix: str or None
        :return: the first ``TriageTagType`` member found, or ``None``
        :rtype: TriageTagType or None
        """
        pattern = (
            _TT_PATTERN
            if comment_prefix is None
            else re.escape(comment_prefix) + r".*?" + _TT_PATTERN
        )
        match = re.search(pattern, line)
        if not match:
            return None

        tag_text = match.group(1)
        member_name = _TT_STR_TO_NAME[tag_text]
        return getattr(cls, member_name)
