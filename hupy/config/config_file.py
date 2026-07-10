"""
config_file.py

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
    def _validate_version_grep_hook(self):
        """
        warn once, at creation, when the version grep hook is unset;
        otherwise error if ``version_file`` does not point to a real
        file.
        """
        if self.is_unconfigured():
            renderer = AnsiRenderer(sys.stdout)
            logger.warning(
                "VerGrep not configured:\nmust set {}, {} to enable".format(
                    renderer.color("version_file", AnsiStyle.BOLD),
                    renderer.color("version_line_pattern", AnsiStyle.BOLD),
                )
            )
            return self

        logger.debug("version_file:\t{}".format(self.version_file))
        logger.debug(
            "version_line_pattern:\t{}".format(self.version_line_pattern)
        )

        if not self.version_file.exists():
            try:
                raise FileNotFoundError(
                    "version file not found: {}".format(self.version_file)
                )
            except FileNotFoundError as e:
                logger.exception("version file not found")
                raise SystemExit(1) from e

        return self


class _Cbm(BaseModel):
    """
    configuration for the CBM module (commit, branch, and merge types)
    """

    main_branch_name: str = Field(default="main", min_length=1)
    dev_branch_name: str = Field(default="dev", min_length=1)
    hotfix_branch_prefix: str = Field(default="hotfix", min_length=1)
    release_branch_prefix: str = Field(default="release", min_length=1)


class _Pch(BaseModel):
    """
    configuration for the PCH module (pre-commit hook)
    """

    enable_vertical_slice: bool = False
    enable_pre_alpha: bool = True
    alpha_tag: str = "-alpha"
    beta_tag: str = "-beta"
    release_candidate_tag: str = "-rc"


class _Bdc(BaseModel):
    """
    configuration for the BDC module (ban direct commit)
    """

    ban_commit_to_main: bool = True
    ban_commit_to_dev: bool = False
    ban_commit_to_branches: list[str] = Field(default_factory=list)


class HupyConfigFile(BaseModel):
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    hupy_version: str = Field(default_factory=lambda: version("HUPy"))
    default_logger_verbosity: int = 1
    ver_grep: _VerGrep = Field(default_factory=_VerGrep)
    cbm: _Cbm = Field(default_factory=_Cbm)
    pch: _Pch = Field(default_factory=_Pch)
    bdc: _Bdc = Field(default_factory=_Bdc)
