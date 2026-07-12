"""
update_stubs.py

dynamically generate & write git hook stub scripts into a repo's
hooks directory: content is rendered in-process from each registered
hook stage's ``HOOK_NAME``, no on-disk template files or placeholder
substitution involved
"""

import sys

from hupy.kamilog import getLogger
from hupy.stub import STUB_LOGGER_NAME
from hupy.stub.names_by_demand import get_hook_names_by_demand

# logger  ######################################################################

logger = getLogger(STUB_LOGGER_NAME)
logger.propagate = False

# constants  ###################################################################

_STUB_TEMPLATE = """#!/usr/bin/env bash
"{python}" -m hupy hook {hook_name} "$@"
"""

_STUB_MODE = 0o755


# Public API  ##################################################################


def update_hooks_stub(hooks_dir, force=False, is_init=False, update=False):
    """
    dynamically generate and write every hook stub demanded by
    ``get_hook_names_by_demand`` into ``hooks_dir``.


    :param hooks_dir: directory the hook stub scripts are written into
    :type hooks_dir: pathlib.Path
    :param force: whether overwrite a hook stub already present in ``hooks_dir``
    :type force: bool, optional
    :param is_init: whether called from the ``init`` subcommand
    :type is_init: bool, optional
    :param update: whether called to update stubs already installed
    :type update: bool, optional
    :raises SystemExit: a hook stub already exists in ``hooks_dir`` and
            ``force`` is ``False``
    """
    logger.enter("update hook stubs")
    logger.debug("hooks dir: {}".format(hooks_dir))

    hooks_dir.mkdir(parents=True, exist_ok=True)
    # FIXME mpv interaction & logger print

    for hook_name in get_hook_names_by_demand():
        target_path = hooks_dir / hook_name

        if target_path.exists():
            if not force:
                logger.error(
                    "hook already exists (use --force to override): {}".format(
                        target_path
                    )
                )
                raise SystemExit(1)

            logger.warning("overwrite existing hook: {}".format(target_path))

        target_path.write_text(
            _STUB_TEMPLATE.format(python=sys.executable, hook_name=hook_name),
            encoding="utf-8",
        )
        target_path.chmod(_STUB_MODE)

        logger.debug("hook stub installed: {}".format(target_path))


# TODO summary logger
