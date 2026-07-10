"""
__init__.py

triage tag gating module
"""

from hupy import PROJ_LOGGER_NAME

TTG_LOGGER_NAME = PROJ_LOGGER_NAME + ".TTG"

from .gate_tt import perform_triage_tags_gating

__all__ = ("perform_triage_tags_gating",)
