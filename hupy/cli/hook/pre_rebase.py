"""
pre_rebase.py

define the pre-rebase stage's identity, run by the generic hook stage
runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "pre-rebase"
DOC = "run pre-rebase stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
