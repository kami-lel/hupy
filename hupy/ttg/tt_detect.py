################################################################################
# hupy/tt_detect.py
#
# triage tag detection and grouping utilities
################################################################################

from enum import Flag, auto


class TriageTag(Flag):  # ======================================================
    """
    triage tag flags in three tiers (Loud, Steady, Quiet)
    """

    # TT instances  ------------------------------------------------------------

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
