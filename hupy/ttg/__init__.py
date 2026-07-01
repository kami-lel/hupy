"""
__init__.py

triage tag gating and commit type detection module
"""

from .tt_gating import perform_triage_tags_gating

__all__ = ("perform_triage_tags_gating",)
