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

    logger_verbosity: int = 1  # FIXME change better name
    skip_once: set[str] = Field(default_factory=set)

    def consume_skip_once(self, module_abbr):
        """
        check ``module_abbr`` against ``skip_once``. the flag stays
        set for the rest of the round, since a module may be checked
        multiple times in one round (eg ``hb``'s lead/trail brackets
        across both hook stages); call ``clear_skip_once`` once the
        round finishes to spend it.


        :param module_abbr: module abbreviation, eg ``"bdc"``
        :type module_abbr: str
        :return: ``True`` if ``module_abbr`` is flagged
        :rtype: bool
        """
        return module_abbr in self.skip_once

    def clear_skip_once(self):
        """
        empty ``skip_once``, spending every flag now that the round
        has finished


        :rtype: None
        """
        self.skip_once.clear()
