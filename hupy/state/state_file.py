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

    hooks_logger_verbosity: int = 1
    skip_once: set[str] = Field(default_factory=set)

    def reset_for_next_commit(self):
        """
        empty ``skip_once``, spending every flag now that the round has finished
        """
        self.skip_once.clear()
