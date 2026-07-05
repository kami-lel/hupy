"""
model.py

define the HUPy config schema (``.hupy.config.json``) as a pydantic
model, providing default values used when writing a fresh config file
"""

import pathlib
from importlib.metadata import version

from pydantic import BaseModel, Field

__all__ = ("HupyConfig",)


class _VerGrep(BaseModel):
    """
    configuration for version grep hook
    """

    # todo validate ver grep file existed etc.

    version_file: pathlib.Path = pathlib.Path("")
    version_line_pattern: str = ""


class HupyConfig(BaseModel):
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    hupy_version: str = Field(default_factory=lambda: version("HUPy"))
    default_logger_verbosity: int = 1
    ver_grep: _VerGrep = Field(
        default_factory=_VerGrep
    )
