"""
pre_commit.py

define the pre-commit stage's identity and ``run_core``, run by the
generic hook stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.bdc.ban_direct_commit import ban_direct_commit
from hupy.ttg.gate_tt import perform_triage_tags_gating

# constants  ###################################################################
HOOK_NAME = "pre-commit"
DOC = "run pre-commit stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False


# Public API  ##################################################################
def run_core(repo, state_file):
    """
    execute direct-commit ban and triage tag gating.
    """
    ban_direct_commit(repo, state_file)
    perform_triage_tags_gating(repo, state_file)
