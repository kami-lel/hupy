"""
state_file.py

define the HUPy state schema (``hupy-state.json``) as a pydantic
model
"""

from pydantic import BaseModel, Field

__all__ = ("HupyStateFile",)


# data structure  ##############################################################


class HupyStateFile(BaseModel):
    """
    schema for the HUPy state file (``hupy-state.json``)
    """

    logger_verbosity: int = 1
    skip_once: list[str] = Field(default_factory=list)
