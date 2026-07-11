"""
open_state.py

define ``open_state_file``
"""

import contextlib
import fcntl
import json
import os
import tempfile
import threading

from pydantic import ValidationError

from hupy.kamilog import getLogger
from hupy.state import STATE_LOGGER_NAME
from hupy.state.state_file import HupyStateFile
from hupy.state.state_file_path import get_state_file_path

__all__ = ("open_state_file",)

logger = getLogger(STATE_LOGGER_NAME)
logger.propagate = False


# lock  ########################################################################

_STATE_LOCK = threading.Lock()

_LOCK_FILE_SUFFIX = ".lock"


# auxiliary  ###################################################################


def _load_state(state_path):
    """
    load ``state_path`` into a :class:`HupyStateFile`, falling back to a
    fresh default instance when the file is absent or corrupt; a corrupt
    file is overwritten on the next save so commits are never blocked


    :param state_path: path to the HUPy state file
    :type state_path: pathlib.Path
    :return: the loaded state, or a default instance on absence/corruption
    :rtype: HupyStateFile
    """
    if not state_path.exists():
        logger.info(
            "missing hupy-state.json, create from defaults:\t{}".format(
                state_path
            )
        )
        return HupyStateFile()

    try:
        return HupyStateFile(**json.loads(state_path.read_text()))
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValidationError,
        TypeError,
    ) as e:
        logger.warning(
            "hupy-state.json corrupt, reset to defaults:\t{}\n{}".format(
                state_path, e
            )
        )
        return HupyStateFile()


# Public API  ##################################################################
@contextlib.contextmanager
def open_state_file(repo):
    """
    open ``repo``'s HUPy state file as a validated
    :class:`HupyStateFile`, atomically saving it back on exit
    (thread- and process-safe)

    :param repo: git repository object
    :type repo: git.Repo
    :yield: the open state object
    :rtype: HupyStateFile
    """
    state_path = get_state_file_path(repo)
    lock_path = state_path.with_name(state_path.name + _LOCK_FILE_SUFFIX)

    with _STATE_LOCK, open(lock_path, "w", encoding="utf-8") as lock_file:
        logger.debug("acquire HUPy state file lock: {}".format(lock_path))
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        try:
            logger.debug("open HUPy state file: {}".format(state_path))
            state = _load_state(state_path)

            yield state

            fd, tmp_name = tempfile.mkstemp(
                dir=state_path.parent, prefix=state_path.name + "."
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                    tmp_file.write(state.model_dump_json(indent=2))
                os.replace(tmp_name, state_path)
            except BaseException:
                os.remove(tmp_name)
                raise

            logger.debug("HUPy state file saved: {}".format(state_path))
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
