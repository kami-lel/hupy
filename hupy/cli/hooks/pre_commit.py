"""
pre_commit.py

define the pre-commit stage's identity and ``run_features``, run by
the generic hook stage runner in ``cli_hook.py``
"""

from hupy.bdc.ban_direct_commit import ban_direct_commit
from hupy.pt.perform_paper_trail import perform_paper_trail
from hupy.ttg.gate_tt import perform_triage_tags_gating

# constants  ###################################################################
HOOK_NAME = "pre-commit"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger, hooks_args):
    """
    execute direct-commit ban, triage tag gating, and paper trail.
    """
    ban_direct_commit(repo, state_file)
    perform_triage_tags_gating(repo, state_file)
    perform_paper_trail(repo, state_file, HOOK_NAME, hooks_args)
