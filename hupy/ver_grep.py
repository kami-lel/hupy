from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import getLogger

# logger  ######################################################################
logger = getLogger(PROJ_LOGGER_NAME + ".VerGrep")
logger.propagate = False


# Public API  ##################################################################


def grep_repo_version():
    pass  # TODO find version feature
