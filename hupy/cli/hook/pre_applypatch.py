"""
pre_applypatch.py

define the pre-applypatch stage's identity, run by the generic hook
stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "pre-applypatch"
DOC = "run pre-applypatch stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
