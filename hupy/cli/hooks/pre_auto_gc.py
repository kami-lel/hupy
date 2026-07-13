"""
pre_auto_gc.py

define the pre-auto-gc stage's identity, run by the generic hook
stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "pre-auto-gc"
DOC = "run pre-auto-gc stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
