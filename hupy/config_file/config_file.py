"""
config_file.py

define the HUPy config schema (``.hupy.config.json``) as a pydantic
model
"""

import pathlib
import sys
from importlib.metadata import version

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from hupy.cbm.commit_type import CommitType
from hupy.config_file import CONFIG_LOGGER_NAME
from hupy.kamilog import getLogger

__all__ = ("HupyConfigFile",)


# logger  ######################################################################


logger = getLogger(CONFIG_LOGGER_NAME)
logger.propagate = False


# internal structures  #########################################################


class _VerGrep(BaseModel):  # ==================================================
    """
    configuration for version grep hook
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    is_disabled: bool

    version_file: pathlib.Path
    version_line_pattern: str


class _Cbm(BaseModel):  # ======================================================
    """
    configuration for the CBM module (commit, branch, and merge types)
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    main_branch_name: str = Field(min_length=1)
    dev_branch_name: str = Field(min_length=1)
    hotfix_branch_prefix: str = Field(min_length=1)
    release_branch_prefix: str = Field(min_length=1)


class _Bdc(BaseModel):  # ======================================================
    """
    configuration for the BDC module (ban direct commit)
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    is_disabled: bool
    ban_commit_to_main: bool
    ban_commit_to_dev: bool
    ban_commit_to_branches: list[str]


class _Ttg(BaseModel):  # ======================================================
    """
    configuration for Triage Tag Gating
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    is_disabled: bool
    disable_tt_detect_by_type: bool
    ignored_path_globs: list[str]


class _Pch(BaseModel):  # ======================================================
    """
    configuration for the PCH module (pre-commit hook)
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    is_disabled: bool

    enable_vertical_slice: bool
    enable_pre_alpha: bool
    alpha_tag: str
    beta_tag: str
    release_candidate_tag: str


# Hook Bracket  ================================================================
class _HbCmd(BaseModel):
    """
    a single bracketed command run alongside a HUPy git hook
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    cmd: str
    allow_commit_types: CommitType = CommitType(0)
    allow_failure: bool = False
    remark: str = ""

    # validators  --------------------------------------------------------------

    @field_validator("allow_commit_types", mode="before")
    @classmethod
    def _parse_allow_commit_types(cls, filters):
        """
        merge the config list of member names into a single
        ``CommitType`` allow list instance; a non-list value (eg an
        already-parsed instance) passes through to pydantic


        :param filters: commit type member names, or a ready value
        :type filters: list[str] or CommitType or int
        :return: the merged allow list instance, or ``filters`` as-is
        :rtype: CommitType or object
        """
        if not isinstance(filters, list):
            return filters

        result = CommitType(0)
        for name in filters:
            try:
                result |= CommitType[name]
            except KeyError:
                logger.warning("illegal commit type name: {}".format(name))

        return result


class _HbBracket(BaseModel):
    """
    lead/trail commands bracketing one HUPy git hook
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    lead: list[_HbCmd] = Field(default_factory=list)
    trail: list[_HbCmd] = Field(default_factory=list)


class _Hb(BaseModel):
    """
    configuration for the HB module (hook bracket)
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    is_disabled: bool
    pre_commit: _HbBracket
    prepare_commit_msg: _HbBracket
    post_commit: _HbBracket

    # Public Method  -----------------------------------------------------------

    def get_bracket(self, hook_name):
        """
        :param hook_name: hook name, eg ``"pre-commit"``
        :type hook_name: str
        :return: bracket for ``hook_name``, or ``None`` if unrecognized
        :rtype: _HbBracket or None
        """
        return {
            "pre-commit": self.pre_commit,
            "prepare-commit-msg": self.prepare_commit_msg,
            "post-commit": self.post_commit,
        }.get(hook_name)


class HupyConfigFile(BaseModel):  ##############################################
    """
    schema for the HUPy config file (``.hupy.config.json``)
    """

    model_config = ConfigDict(extra="forbid")

    # fields  ------------------------------------------------------------------

    hupy_version: str
    vg: _VerGrep
    cbm: _Cbm
    bdc: _Bdc
    ttg: _Ttg
    pch: _Pch
    hb: _Hb

    # validators  --------------------------------------------------------------

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
