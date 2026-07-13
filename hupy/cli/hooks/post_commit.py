"""
post_commit.py

define the post-commit stage's identity and ``run_after``, run
by the generic hook stage runner in ``cli_hook.py``
"""

# constants  ###################################################################
HOOK_NAME = "post-commit"


# Public API  ##################################################################
def run_after(repo, state_file, proj_logger, logger):
    """
    reset one-time state for the next commit, then log that the
    full HUPy hook round has finished.
    """
    state_file.reset_for_next_commit()
    # Fixme be flow aware
    proj_logger.done("all HUPy hooks finished")
