"""
post_index_change.py

define the post-index-change stage's identity, run by the generic
hook stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "post-index-change"
DOC = "run post-index-change stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
