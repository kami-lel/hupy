"""
post_applypatch.py

define the post-applypatch stage's identity, run by the generic hook
stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "post-applypatch"
DOC = "run post-applypatch stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
