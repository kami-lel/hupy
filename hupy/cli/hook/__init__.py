"""
__init__.py

hook package: git hook stage subcommands for HUPy
"""

# constants  ###################################################################
HOOK_STAGE_START = "Start"
HOOK_STAGE_NOOP = "No Operation in this HUPy version"
HOOK_STAGE_FINISHED = "Finished"

__all__ = ("HOOK_STAGE_START", "HOOK_STAGE_NOOP", "HOOK_STAGE_FINISHED")
