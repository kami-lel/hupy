"""
names_by_demand.py

decide which git hook names actually need an installed stub
"""

__all__ = ("get_hook_names_by_demand",)


from hupy.kamilog import getLogger
from hupy.stub import STUB_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(STUB_LOGGER_NAME)
logger.propagate = False

# Public API  ##################################################################


def get_hook_names_by_demand():
    """
    :return: hook names that should have an installed stub
    :rtype: list[str]
    """
    # FIXME mpl names by demand
    names = [
        "pre-commit",
        "prepare-commit-msg",
        "post-commit",
    ]

    logger.debug("demanded hook names:\n{}".format(", ".join(names)))
    return names
