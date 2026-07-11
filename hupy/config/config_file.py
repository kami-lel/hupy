"""
config_file.py

define the HUPy config schema (``.hupy.config.json``) as a pydantic
model
"""

import pathlib
import sys
from importlib.metadata import version

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

    is_disabled: bool

    version_file: pathlib.Path
    version_line_pattern: str

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
        if self.is_disabled:
            return self

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

    main_branch_name: str = Field(min_length=1)
    dev_branch_name: str = Field(min_length=1)
    hotfix_branch_prefix: str = Field(min_length=1)
    release_branch_prefix: str = Field(min_length=1)


class _Bdc(BaseModel):
    """
    configuration for the BDC module (ban direct commit)
    """

    is_disabled: bool
    ban_commit_to_main: bool
    ban_commit_to_dev: bool
    ban_commit_to_branches: list[str]


class _Ttg(BaseModel):
    """
    configuration for Triage Tag Gating
    """

    is_disabled: bool
    disable_tt_detect_by_type: bool
    ignored_path_globs: list[str]


class _Pch(BaseModel):
    """
    configuration for the PCH module (pre-commit hook)
    """

    is_disabled: bool

    enable_vertical_slice: bool
    enable_pre_alpha: bool
    alpha_tag: str
    beta_tag: str
    release_candidate_tag: str


class _Hb(BaseModel):
    """
    configuration for the HB module (hook bracket)
    """

    is_disabled: bool
    pre_commit: list[str]
    prepare_commit_msg: list[str]


class HupyConfigFile(BaseModel):
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    hupy_version: str
    vg: _VerGrep
    cbm: _Cbm
    bdc: _Bdc
    ttg: _Ttg
    pch: _Pch
    hb: _Hb

    @model_validator(mode="after")
    def _validate_hupy_version(self):
        """
        error if ``hupy_version`` mismatches the installed HUPy version
        """
        current_version = version("HUPy")
        if self.hupy_version != current_version:
            logger.warning(
                "version mismatch:\n"
                "config file version:\t{}\n"
                "installed HUPy version:\t{}".format(
                    self.hupy_version, current_version
                )
            )

        return self
