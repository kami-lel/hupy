"""
PT module

Paper Trail — assert files matching a configured glob were changed
alongside a HUPy git hook
"""

from hupy import PROJ_LOGGER_NAME

# constants  ###################################################################
PT_LOGGER_NAME = PROJ_LOGGER_NAME + ".PT"

from hupy.pt.perform_paper_trail import perform_paper_trail

__all__ = ("PT_LOGGER_NAME", "perform_paper_trail")
