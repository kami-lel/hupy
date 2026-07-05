"""
load_config.py

load the HUPy config file (``.hupy.config.json``) from a repo root,
validating it against :class:`HupyConfig`
"""

import pathlib

from pydantic import ValidationError

from hupy import PROJ_LOGGER_NAME
from hupy.config import CONFIG_FILENAME
from hupy.config.model import HupyConfig
from hupy.kamilog import getLogger

__all__ = ("load_hupy_config",)


# logger  ######################################################################


logger = getLogger(PROJ_LOGGER_NAME)


# Public API  ##################################################################


# TODO make singleton/static
# TODO hupy takes a repo?


def load_hupy_config(repo_root):
    """
    load and validate the HUPy config file (``.hupy.config.json``) at
    ``repo_root``; exits the process if the file is missing or
    malformed
    """
    config_path = pathlib.Path(repo_root) / CONFIG_FILENAME

    try:
        return HupyConfig.model_validate_json(config_path.read_text())
    except FileNotFoundError as e:
        logger.error("HUPy config file not found: {}".format(config_path))
        raise SystemExit(1) from e
    except ValidationError as e:
        logger.error(
            "HUPy config file is malformed: {}\n{}".format(config_path, e)
        )
        raise SystemExit(1) from e
