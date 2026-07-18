"""
pre_applypatch.py

define the pre-applypatch stage's identity and ``run_features``, run
by the generic hook stage runner in ``cli_hook.py``
"""

from hupy.bdc.ban_direct_commit import ban_direct_commit

# constants  ###################################################################
HOOK_NAME = "pre-applypatch"


# Public API  ##################################################################
def run_features(repo, state_file, proj_logger, logger, hooks_args):
    """
    execute direct-commit ban.
    """
    ban_direct_commit(repo, state_file)
