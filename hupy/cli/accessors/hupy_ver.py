"""
hupy_ver.py

define the ``hupy-version`` accessor key's ``run_get``, printing the
installed HUPy package version
"""

from importlib.metadata import version

from hupy import PROJ_LOGGER_NAME, kamilog

# constants  ###################################################################
KEY = "hupy-version"
DOC = "get the installed HUPy version"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + KEY)
logger.propagate = False


# Public API  ##################################################################
def run_get(args, repo, state_file):
    """
    print the installed HUPy package version.
    """
    logger.done(version("HUPy"))
