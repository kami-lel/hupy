"""
commit_msg.py

define the commit-msg stage's identity, run by the generic hook stage
runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "commit-msg"
DOC = "run commit-msg stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
