"""
pre_commit.py

define the pre-commit stage's identity and ``run_features``, run by
the generic hook stage runner in ``cli_hook.py``
"""

from hupy.bdc.ban_direct_commit import ban_direct_commit
from hupy.ttg.gate_tt import perform_triage_tags_gating

# constants  ###################################################################
HOOK_NAME = "pre-commit"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger):
    """
    execute direct-commit ban and triage tag gating.
    """
    ban_direct_commit(repo, state_file)
    perform_triage_tags_gating(repo, state_file)
