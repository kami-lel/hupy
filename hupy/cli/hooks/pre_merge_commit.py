"""
pre_merge_commit.py

define the pre-merge-commit stage's identity, run by the generic hook
stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "pre-merge-commit"
DOC = "run pre-merge-commit stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
