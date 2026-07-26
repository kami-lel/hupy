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

__all__ = ("sync_config_file", "remove_config_file")

logger = getLogger(PROJ_LOGGER_NAME)


# Public API  ##################################################################
def sync_config_file(repo, force=False, dry_run=False):
    """
    converge ``repo``'s working tree root onto a HUPy config file
    (``.hupy.config.jsonc``).

    an absent config file is always written from the default asset.
    a config file already present is a user's own, meant to differ
    from the default, so it is left alone and only reported unless
    ``force`` is set. ``dry_run`` reports the intended action and
    touches nothing.


    :param repo: repo to write the HUPy config file into
    :type repo: git.Repo
    :param force: whether to overwrite a config file already present;
            default=False
    :type force: bool, optional
    :param dry_run: whether to report the intended action instead of
            writing anything; default=False
    :type dry_run: bool, optional
    """
    logger.enter("sync HUPy config file")
    config_path = get_config_file_path(repo)

    if config_path.exists():
        if not force:
            logger.warning(
                "HUPy config file already exists: {}\n"
                "(use --force to override)".format(config_path)
            )
            return

        if dry_run:
            logger.info(
                "would overwrite HUPy config file: {}".format(config_path)
            )
            return

        logger.warning(
            "overwrite existing HUPy config file: {}".format(config_path)
        )
        shutil.copyfile(DEFAULT_CONFIG_ASSET, config_path)
        return

    if dry_run:
        logger.info("would write HUPy config file: {}".format(config_path))
        return

    logger.debug("HUPy config file written: {}".format(config_path))
    shutil.copyfile(DEFAULT_CONFIG_ASSET, config_path)


def remove_config_file(repo, force):
    """
    remove the HUPy config file (``.hupy.config.jsonc``) from
    ``repo``'s working tree root.

    when ``force`` is not set, the file is not deleted: its presence
    is only reported via a warning (dry run).
    """
    logger.enter("remove HUPy config file")
    config_path = get_config_file_path(repo)

    if not config_path.exists():
        logger.debug("no HUPy config file to remove: {}".format(config_path))
        return

    if force:
        logger.warning("remove HUPy config file: {}".format(config_path))
        config_path.unlink()
    else:
        logger.info(
            "attempt remove config file: {}".format(config_path)
        )
