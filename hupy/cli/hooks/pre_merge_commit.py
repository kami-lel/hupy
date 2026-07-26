"""
pre_merge_commit.py

define the pre-merge-commit stage's identity and ``run_features``,
run by the generic hook stage runner in ``cli_hook.py``
"""

from hupy.pt.perform_paper_trail import perform_paper_trail
from hupy.ttg.gate_tt import perform_triage_tags_gating
from hupy.ver_grep.version_uniformity import check_version_uniformity

# constants  ###################################################################
HOOK_NAME = "pre-merge-commit"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger, hooks_args):
    """
    execute triage tag gating, paper trail, and version uniformity.
    """
    perform_triage_tags_gating(repo, state_file)
    perform_paper_trail(repo, state_file, HOOK_NAME)
    check_version_uniformity(repo, state_file)

