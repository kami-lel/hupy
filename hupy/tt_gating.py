"""
tt_gating.py

implement triage tag (TT) gating
block commits that introduce triage tags on protected branches
"""

from .commit_type import CommitType, get_current_commit_type
from .kamilog import getLogger

logger = getLogger(__name__)


def perform_triage_tags_gating(repo_root):
    """
    execute triage tag gating for the current commit.


    :param repo_root: path to the git repository or any of its
            subdirectories
    :type repo_root: str
    """
    commit_type = get_current_commit_type(repo_root)
    pass  # TODO reimplement TT Gating
