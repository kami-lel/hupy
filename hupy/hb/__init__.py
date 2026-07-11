"""
HB module
"""

from hupy import PROJ_LOGGER_NAME

# constants  ###################################################################
HB_LOGGER_NAME = PROJ_LOGGER_NAME + ".HB"

from hupy.hb.perform_hook_brackets import perform_hook_brackets

__all__ = ("HB_LOGGER_NAME", "perform_hook_brackets")
