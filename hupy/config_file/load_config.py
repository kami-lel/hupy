"""
load_config.py

load the HUPy config file (``.hupy.config.jsonc``) from a repo root,
validating it against :class:`HupyConfigFile`
"""

import json5
from pydantic import ValidationError

from hupy.config_file import CONFIG_LOGGER_NAME
from hupy.config_file.config_file import HupyConfigFile
from hupy.config_file.config_file_path import get_config_file_path
from hupy.kamilog import getLogger

__all__ = ("load_hupy_config",)


# logger  ######################################################################


logger = getLogger(CONFIG_LOGGER_NAME)


# cache  #######################################################################

# pylint: disable-next=invalid-name
_config_cache = {}  # keyed by repo.git_dir


# Public API  ##################################################################
def load_hupy_config(repo, allows_file_not_found=False):
    """
    load and validate the HUPy config file (``.hupy.config.jsonc``)
    from ``repo``, caching the result per repository so it only loads
    from disk once per ``repo``; exits the process if the file is
    malformed, and, unless ``allows_file_not_found`` is set, if it's
    missing.


    :param repo: git repository object
    :type repo: git.Repo
    :param allows_file_not_found: return ``None`` instead of exiting
            when the config file is missing
    :type allows_file_not_found: bool, optional
    :raises SystemExit: config file is malformed, including a ``vg``
            section left at its empty defaults, or the file is
            missing and ``allows_file_not_found`` is not set
    :return: the loaded and validated configuration, or ``None`` if
            missing and ``allows_file_not_found`` is set
    :rtype: HupyConfigFile or None
    """
    git_dir = repo.git_dir
    if git_dir in _config_cache:
        return _config_cache[git_dir]

    config_path = get_config_file_path(repo)

    try:
        _config_cache[git_dir] = HupyConfigFile.model_validate(
            json5.loads(config_path.read_text())
        )
        logger.debug("config file loaded: {}".format(config_path))
        return _config_cache[git_dir]

    except FileNotFoundError as e:
        if allows_file_not_found:
            return None

        logger.error("config file not found: {}".format(config_path))
        raise SystemExit(1) from e
    except ValidationError as e:
        logger.error("config file is malformed: {}\n{}".format(config_path, e))
        raise SystemExit(1) from e
