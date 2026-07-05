"""
write_config.py

write the HUPy config file (``.hupy.config.json``) at a repo root,
generated from :class:`HupyConfig` defaults
"""

from hupy import PROJ_LOGGER_NAME
from hupy.config import CONFIG_FILENAME
from hupy.config.model import HupyConfig
from hupy.kamilog import getLogger

__all__ = ("write_default_config",)

logger = getLogger(PROJ_LOGGER_NAME)


def write_default_config(repo_root, force):
    """
    write the default HUPy config file (``.hupy.config.json``) at
    ``repo_root``, generated from :class:`HupyConfig` defaults
    """
    logger.enter("write HUPy config file")
    config_path = repo_root / CONFIG_FILENAME

    if config_path.exists():
        if not force:
            logger.error(
                "HUPy config file already exists (use --force to override): "
                "{}".format(config_path)
            )
            raise SystemExit(1)

        logger.warning(
            "override existing HUPy config file: {}".format(config_path)
        )

    logger.debug("HUPy config file written: {}".format(config_path))
    config_path.write_text(HupyConfig().model_dump_json(indent=2) + "\n")
