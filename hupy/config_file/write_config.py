"""
write_config.py

copy the default HUPy config asset (``.hupy.config.jsonc``) to a
repo's root as its HUPy config file
"""

import shutil

from hupy import PROJ_LOGGER_NAME
from hupy.config_file.config_file_path import (
    DEFAULT_CONFIG_ASSET,
    get_config_file_path,
)
from hupy.kamilog import getLogger

__all__ = ("create_default_config_file",)

logger = getLogger(PROJ_LOGGER_NAME)


# Public API  ##################################################################
def create_default_config_file(repo, force):
    """
    copy the default HUPy config asset (``.hupy.config.jsonc``) to
    ``repo``'s working tree root as its HUPy config file
    """
    logger.enter("write HUPy config file")
    config_path = get_config_file_path(repo)

    if config_path.exists():
        if not force:
            logger.error(
                "HUPy config file already exists (use --force to override): "
                "{}".format(config_path)
            )
            raise SystemExit(1)

        logger.warning(
            "overwrite existing HUPy config file: {}".format(config_path)
        )

    logger.debug("HUPy config file written: {}".format(config_path))
    shutil.copyfile(DEFAULT_CONFIG_ASSET, config_path)
