"""
load_config.py

load the HUPy config file (``.hupy.config.json``) from a repo root,
validating it against :class:`HupyConfigFile`
"""

import pathlib

from pydantic import ValidationError

from hupy.cli.cli_init import load_git_repo
from hupy.config import CONFIG_FILENAME, CONFIG_LOGGER_NAME
from hupy.config.hupy_config_file import HupyConfigFile
from hupy.kamilog import getLogger

__all__ = ("load_hupy_config",)


# logger  ######################################################################


logger = getLogger(CONFIG_LOGGER_NAME)


# cache  #######################################################################

# pylint: disable-next=invalid-name
_config_cache = None


# Public API  ##################################################################
def load_hupy_config(repo_path):
    """
    load and validate the HUPy config file (``.hupy.config.json``)
    from the Git repository containing ``repo_path``, caching the
    result so it only loads from disk once; exits the process if the
    file is missing or malformed.


    :param repo_path: path to the repo root, or to any path inside it
    :type repo_path: str
    :raises SystemExit: config file not found or is malformed,
            including a ``ver_grep`` section left at its empty
            defaults
    :return: the loaded and validated configuration
    :rtype: HupyConfigFile
    """
    # pylint: disable-next=global-statement
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    repo = load_git_repo(repo_path)
    config_path = pathlib.Path(repo.working_tree_dir) / CONFIG_FILENAME

    try:
        _config_cache = HupyConfigFile.model_validate_json(
            config_path.read_text()
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
