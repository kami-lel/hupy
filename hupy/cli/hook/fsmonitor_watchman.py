"""
fsmonitor_watchman.py

define the fsmonitor-watchman stage's identity, run by the generic
hook stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "fsmonitor-watchman"
DOC = "run fsmonitor-watchman stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
