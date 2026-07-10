"""
write_state.py

write a default-valued HUPy state file (``hupy-state.json``) to a
repo's ``.git`` directory
"""

from hupy.kamilog import getLogger
from hupy.state import STATE_LOGGER_NAME
from hupy.state.state_file import HupyStateFile
from hupy.state.state_file_path import get_state_file_path

__all__ = ("write_default_state_file",)

logger = getLogger(STATE_LOGGER_NAME)


# Public API  ##################################################################
def write_default_state_file(repo, force):
    """
    write a default-valued HUPy state file (``hupy-state.json``) to
    ``repo``'s ``.git`` directory
    """
    logger.enter("write HUPy state file")
    state_path = get_state_file_path(repo)

    if state_path.exists():
        if not force:
            logger.error(
                "HUPy state file already exists (use --force to override): "
                "{}".format(state_path)
            )
            raise SystemExit(1)

        logger.warning(
            "overwrite existing HUPy state file: {}".format(state_path)
        )

    logger.debug("HUPy state file written: {}".format(state_path))
    state_path.write_text(HupyStateFile().model_dump_json(indent=2))
