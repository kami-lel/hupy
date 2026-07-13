"""
post_merge.py

define the post-merge stage's identity, run by the generic hook stage
runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "post-merge"
DOC = "run post-merge stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
