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

# HACK split into 2 files


# logger  ######################################################################

logger = getLogger(STUB_LOGGER_NAME)
logger.propagate = False

# constants  ###################################################################

_STUB_TEMPLATE = """#!/usr/bin/env bash
"{python}" -m hupy hook {hook_name} "$@"
"""

_STUB_MODE = 0o755


# auxiliaries  ##################################################################


def _write_stub(target_path, hook_name, is_overwrite=False):
    """
    render and write the stub script for ``hook_name`` at ``target_path``,
    then mark it executable.
    """
    target_path.write_text(
        _STUB_TEMPLATE.format(python=sys.executable, hook_name=hook_name),
        encoding="utf-8",
    )
    target_path.chmod(_STUB_MODE)

    if is_overwrite:
        logger.warning("overwrite hook stub: {}".format(target_path))
    else:
        logger.debug("hook stub installed: {}".format(target_path))


def _is_managed_stub(target_path):
    """
    report whether ``target_path`` is a HUPy-installed stub for its own
    file name, identified by its rendered ``-m hupy hook <name>`` line;
    distinguishes HUPy stubs from unrelated files (eg git's own
    ``*.sample`` hooks) sharing the hooks dir.


    :param target_path: candidate file to inspect
    :type target_path: pathlib.Path
    :return: whether ``target_path`` is a HUPy-managed stub
    :rtype: bool
    """
    if not target_path.is_file():
        return False

    try:
        content = target_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    return "-m hupy hook {}".format(target_path.name) in content


# Public API  ##################################################################


def create_init_hook_stubs(hooks_dir, force=False):
    """
    create every hook stub demanded by ``get_hook_names_by_demand`` in
    ``hooks_dir``, aborting on the first one already present unless
    ``force`` is set.


    :param hooks_dir: directory the hook stub scripts are created in
    :type hooks_dir: pathlib.Path
    :param force: whether overwrite a hook stub already present in
            ``hooks_dir``
    :type force: bool, optional
    :raises SystemExit: a hook stub already exists in ``hooks_dir`` and
            ``force`` is ``False``
    """
    logger.enter("install hook stubs")
    logger.debug("hooks dir: {}".format(hooks_dir))

    hooks_dir.mkdir(parents=True, exist_ok=True)

    names = get_hook_names_by_demand()

    for hook_name in names:
        target_path = hooks_dir / hook_name

        file_exist = target_path.exists()
        if file_exist:
            if not force:
                logger.error(
                    "hook already exists (use --force to override): {}".format(
                        target_path
                    )
                )
                raise SystemExit(1)

        _write_stub(target_path, hook_name, is_overwrite=file_exist)


def verify_hook_stubs(hooks_dir, force=False, update=False):
    """
    verify ``hooks_dir`` is synced with the hook stubs demanded by
    ``get_hook_names_by_demand``.

    by default, the two are only compared and reported; when
    ``update`` is set, unused stubs are removed and missing ones are
    added, and, if ``force`` is also set, every already-installed
    demanded stub is regenerated.


    :param hooks_dir: directory the hook stub scripts are verified in
    :type hooks_dir: pathlib.Path
    :param force: whether also replace already-installed demanded
            stubs; requires ``update``
    :type force: bool, optional
    :param update: whether sync installed stubs to demand
    :type update: bool, optional
    """
    logger.enter("verify hook stubs")
    logger.debug("hooks dir: {}".format(hooks_dir))

    hooks_dir.mkdir(parents=True, exist_ok=True)

    demanded_set = set(get_hook_names_by_demand())
    installed_set = {p.name for p in hooks_dir.iterdir() if _is_managed_stub(p)}

    missing_names = sorted(demanded_set - installed_set)
    unused_names = sorted(installed_set - demanded_set)

    if not update:
        for hook_name in missing_names:
            logger.warning(
                "missing hook stub: {}".format(hooks_dir / hook_name)
            )

        for hook_name in unused_names:
            logger.warning(
                "hook stub no longer demanded: {}".format(hooks_dir / hook_name)
            )

        return

    for hook_name in unused_names:
        target_path = hooks_dir / hook_name
        logger.warning("remove unused hook stub: {}".format(target_path))
        target_path.unlink()

    for hook_name in missing_names:
        target_path = hooks_dir / hook_name
        _write_stub(target_path, hook_name)

    if force:
        for hook_name in sorted(demanded_set & installed_set):
            target_path = hooks_dir / hook_name
            _write_stub(target_path, hook_name, is_overwrite=True)
