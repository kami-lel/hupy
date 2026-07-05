"""
model.py

define the HUPy config schema (``.hupy.config.json``) as a pydantic
model, providing default values used when writing a fresh config file
"""

from importlib.metadata import version

from pydantic import BaseModel, Field

__all__ = ("HupyConfig",)


class HupyConfig(BaseModel):
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    logger_verbosity: int = 1
    hupy_version: str = Field(default_factory=lambda: version("HUPy"))
