"""
load_config.py

load the HUPy config file (``.hupy.config.jsonc``) from a repo root,
validating it against :class:`HupyConfigFile`
"""

import json5
from pydantic import ValidationError

from hupy.config import CONFIG_LOGGER_NAME
from hupy.config.config_file import HupyConfigFile
from hupy.config.config_file_path import get_config_file_path
from hupy.kamilog import getLogger

__all__ = ("load_hupy_config",)


# logger  ######################################################################


logger = getLogger(CONFIG_LOGGER_NAME)


# cache  #######################################################################

# pylint: disable-next=invalid-name
_config_cache = None


# Public API  ##################################################################
def load_hupy_config(repo):
    """
    load and validate the HUPy config file (``.hupy.config.jsonc``)
    from ``repo``, caching the result so it only loads from disk
    once; exits the process if the file is missing or malformed.


    :param repo: git repository object
    :type repo: git.Repo
    :raises SystemExit: config file not found or is malformed,
            including a ``vg`` section left at its empty
            defaults
    :return: the loaded and validated configuration
    :rtype: HupyConfigFile
    """
    # pylint: disable-next=global-statement
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    config_path = get_config_file_path(repo)

    try:
        _config_cache = HupyConfigFile.model_validate(
            json5.loads(config_path.read_text())
        )
        return _config_cache

    except FileNotFoundError as e:
        logger.error("HUPy config file not found: {}".format(config_path))
        raise SystemExit(1) from e
    except ValidationError as e:
        logger.error(
            "HUPy config file is malformed: {}\n{}".format(config_path, e)
        )
        raise SystemExit(1) from e
