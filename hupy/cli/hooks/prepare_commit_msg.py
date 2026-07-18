"""
prepare_commit_msg.py

define the prepare-commit-msg stage's identity and ``run_features``,
run by the generic hook stage runner in ``cli_hook.py``
"""

from hupy.pch.prepend_commit_header import prepend_commit_header

# constants  ###################################################################
HOOK_NAME = "prepare-commit-msg"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger, hooks_args):
    """
    execute prepend commit header.
    """
    prepend_commit_header(repo, state_file)
