"""
sendemail_validate.py

define the sendemail-validate stage's identity, run by the generic
hook stage runner in ``cli_hook.py``
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
HOOK_NAME = "sendemail-validate"
DOC = "run sendemail-validate stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + HOOK_NAME)
logger.propagate = False
