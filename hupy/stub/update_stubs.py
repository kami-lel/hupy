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


# auxiliaries  ##################################################################


def _write_stub(target_path, hook_name):
    """
    render and write the stub script for ``hook_name`` at ``target_path``,
    then mark it executable.
    """
    target_path.write_text(
        _STUB_TEMPLATE.format(python=sys.executable, hook_name=hook_name),
        encoding="utf-8",
    )
    target_path.chmod(_STUB_MODE)


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


def _init_hooks_stub(hooks_dir, demanded_names, force):
    """
    ``is_init`` path: create every demanded stub, aborting on the first
    one already present unless ``force`` is set.
    """
    for hook_name in demanded_names:
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

        _write_stub(target_path, hook_name)
        logger.debug("hook stub installed: {}".format(target_path))


def _sync_hooks_stub(hooks_dir, demanded_names, force, update):
    """
    non-``is_init`` path: report sync status between ``hooks_dir`` and
    ``demanded_names``, applying ``update``/``force`` per
    :func:`update_hooks_stub`.
    """
    demanded_set = set(demanded_names)
    installed_set = {p.name for p in hooks_dir.iterdir() if _is_managed_stub(p)}

    missing_names = sorted(demanded_set - installed_set)
    unused_names = sorted(installed_set - demanded_set)

    if not update:
        for hook_name in missing_names:
            logger.warning(
                "hook stub missing: {}".format(hooks_dir / hook_name)
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
        logger.debug("hook stub installed: {}".format(target_path))

    if force:
        for hook_name in sorted(demanded_set & installed_set):
            target_path = hooks_dir / hook_name
            logger.warning(
                "replacing existing hook stub: {}".format(target_path)
            )
            _write_stub(target_path, hook_name)


# Public API  ##################################################################


def update_hooks_stub(hooks_dir, force=False, is_init=False, update=False):
    """
    sync ``hooks_dir`` against the hook stubs demanded by
    ``get_hook_names_by_demand``.

    when ``is_init``, every demanded stub is created, aborting on the
    first one already present unless ``force`` is set (``update`` is
    ignored); otherwise, the two directories are only compared and
    reported unless ``update`` is set, in which case unused stubs are
    removed and missing ones are added, and, if ``force`` is also set,
    every already-installed demanded stub is regenerated.


    :param hooks_dir: directory the hook stub scripts are synced into
    :type hooks_dir: pathlib.Path
    :param force: when ``is_init``, whether overwrite a hook stub already
            present in ``hooks_dir``; otherwise, whether also replace
            already-installed demanded stubs (requires ``update``)
    :type force: bool, optional
    :param is_init: whether called from the ``init`` subcommand
    :type is_init: bool, optional
    :param update: whether sync installed stubs to demand;
            ignored when ``is_init``
    :type update: bool, optional
    :raises SystemExit: ``is_init`` is set, a hook stub already exists in
            ``hooks_dir``, and ``force`` is ``False``
    """
    # FIXME FIXME simplify interactions & keeps upd interaction
    logger.enter("update hook stubs")
    logger.debug("hooks dir: {}".format(hooks_dir))

    hooks_dir.mkdir(parents=True, exist_ok=True)

    demanded_names = get_hook_names_by_demand()

    if is_init:
        _init_hooks_stub(hooks_dir, demanded_names, force)
    else:
        _sync_hooks_stub(hooks_dir, demanded_names, force, update)
