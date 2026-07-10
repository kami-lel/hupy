"""
state_file.py

define the HUPy state schema (``hupy-state.json``) as a pydantic
model
"""

from pydantic import BaseModel

__all__ = ("HupyStateFile",)


# data structure  ##############################################################


class HupyStateFile(BaseModel):
    """
    schema for the HUPy state file (``hupy-state.json``)
    """
