"""
pre_merge_commit.py

define the pre-merge-commit stage's identity and ``run_core``, run by
the generic hook stage runner in ``cli_hook.py``
"""

from hupy.ttg.gate_tt import perform_triage_tags_gating

# constants  ###################################################################
HOOK_NAME = "pre-merge-commit"


# Public API  ##################################################################
def run_core(repo, state_file, proj_logger, logger):
    """
    execute triage tag gating.
    """
    perform_triage_tags_gating(repo, state_file)

