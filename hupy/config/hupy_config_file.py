"""
hupy_config_file.py

define the HUPy config schema (``.hupy.config.json``) as a pydantic
model, providing default values used when writing a fresh config file
"""

import pathlib
from importlib.metadata import version
import sys

from pydantic import BaseModel, Field, model_validator

from hupy.config import CONFIG_LOGGER_NAME
from hupy.kamilog import AnsiRenderer, AnsiStyle, getLogger

__all__ = ("HupyConfigFile",)


# logger  ######################################################################


logger = getLogger(CONFIG_LOGGER_NAME)
logger.propagate = False


# data structure  ##############################################################


class _VerGrep(BaseModel):
    """
    configuration for version grep hook
    """

    # Todo validate ver grep file existed etc.

    version_file: pathlib.Path = pathlib.Path("")
    version_line_pattern: str = ""

    def is_unconfigured(self):
        """
        :return: if ``version_file`` or ``version_line_pattern`` is unset
        :rtype: bool
        """
        return (
            str(self.version_file) in ("", ".")
            or not self.version_line_pattern.strip()
        )

    @model_validator(mode="after")
    def _warn_if_unconfigured(self):
        """
        warn once, at creation, when the version grep hook is unset.
        """
        renderer = AnsiRenderer(sys.stdout)
        if self.is_unconfigured():
            logger.warning(
                "VerGrep not configured:\nmust set {}, {} to enable".format(
                    renderer.color("version_file", AnsiStyle.BOLD),
                    renderer.color("version_line_pattern", AnsiStyle.BOLD),
                )
            )
        return self


class HupyConfigFile(BaseModel):
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    hupy_version: str = Field(default_factory=lambda: version("HUPy"))
    default_logger_verbosity: int = 1
    ver_grep: _VerGrep = Field(default_factory=_VerGrep)
