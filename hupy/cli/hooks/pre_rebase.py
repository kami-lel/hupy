"""
pre_rebase.py

define the pre-rebase stage's identity and ``run_features``, run by
the generic hook stage runner in ``cli_hook.py``
"""

from hupy.bdc.ban_direct_commit import ban_direct_commit
from hupy.pt.perform_paper_trail import perform_paper_trail

# constants  ###################################################################
HOOK_NAME = "pre-rebase"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger, hooks_args):
    """
    execute direct-commit ban and paper trail.
    """
    ban_direct_commit(repo, state_file)
    perform_paper_trail(repo, state_file, HOOK_NAME, hooks_args)

