"""
pre_merge_commit.py

define the pre-merge-commit stage's identity and ``run_features``,
run by the generic hook stage runner in ``cli_hook.py``
"""

from hupy.pt.perform_paper_trail import perform_paper_trail
from hupy.ttg.gate_tt import perform_triage_tags_gating

# constants  ###################################################################
HOOK_NAME = "pre-merge-commit"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger, hooks_args):
    """
    execute triage tag gating and paper trail.
    """
    perform_triage_tags_gating(repo, state_file)
    perform_paper_trail(repo, state_file, HOOK_NAME, hooks_args)

