"""
tt_gating.py

implement triage tag (TT) gating — block commits that introduce
*Loud* triage tags (``TODO``, ``FIXME``, ``HACK``, ``BUG``) on
protected branches, with per-tag and per-branch configurability
"""

from .commit_type import CommitType, get_current_commit_type

# TODO reimplement TT Gating
