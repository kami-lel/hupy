"""
post_commit.py

define the post-commit stage's identity, ``run_after``, and
``run_done``, run by the generic hook stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "post-commit"
DOC = "run post-commit stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
proj_root_logger = kamilog.getLogger(PROJ_LOGGER_NAME)


# Public API  ##################################################################
def run_after(repo, state_file):
    """
    reset one-time state for the next commit, then log that the
    full HUPy hook round has finished.
    """
    state_file.reset_for_next_commit()


def run_done(repo, state_file):
    """
    log that the full HUPy hook round has finished.
    """
    proj_root_logger.done("all HUPy hooks finished")
