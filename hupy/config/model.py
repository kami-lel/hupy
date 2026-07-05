"""
model.py

define the HUPy config schema (``.hupy.config.json``) as a pydantic
model, providing default values used when writing a fresh config file
"""

import pathlib
from importlib.metadata import version

from pydantic import BaseModel, Field, field_validator

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import getLogger

__all__ = ("HupyConfig", "VER_GREP_LOGGER_NAME")


# logger  ######################################################################


VER_GREP_LOGGER_NAME = PROJ_LOGGER_NAME + ".VerGrep"

ver_grep_logger = getLogger(VER_GREP_LOGGER_NAME)


# data structure  ##############################################################


class _VerGrep(BaseModel):
    """
    configuration for version grep hook
    """

    # todo validate ver grep file existed etc.

    version_file: pathlib.Path = pathlib.Path("")
    version_line_pattern: str = ""

    @field_validator("version_file", "version_line_pattern")
    @classmethod
    def validate_configured(cls, v):
        if not str(v).strip():
            ver_grep_logger.exception(
                "version_file and version_line_pattern must be configured"
            )
        return v


class HupyConfig(BaseModel):
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    hupy_version: str = Field(default_factory=lambda: version("HUPy"))
    default_logger_verbosity: int = 1
    ver_grep: _VerGrep = Field(default_factory=_VerGrep)
