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
    skip_once: set[str] = Field(default_factory=set)

    def consume_skip_once(self, module_abbr):
        """
        check ``module_abbr`` against ``skip_once``, discarding it if
        present so the flag is spent after this call.


        :param module_abbr: module abbreviation, eg ``"bdc"``
        :type module_abbr: str
        :return: ``True`` if ``module_abbr`` was flagged
        :rtype: bool
        """
        if module_abbr not in self.skip_once:
            return False

        self.skip_once.discard(module_abbr)
        return True
