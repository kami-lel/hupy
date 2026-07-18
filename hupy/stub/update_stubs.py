"""
update_stubs.py

dynamically generate & write git hook stub scripts into a repo's
hooks directory: content is rendered in-process from each registered
hook stage's ``HOOK_NAME``, no on-disk template files or placeholder
substitution involved
"""

import pathlib
import sys

from hupy.kamilog import getLogger
from hupy.stub import STUB_LOGGER_NAME
from hupy.stub.names_by_demand import get_hook_names_by_demand

# logger  ######################################################################

logger = getLogger(STUB_LOGGER_NAME)
logger.propagate = False

# constants  ###################################################################

_STUB_TEMPLATE = """#!/usr/bin/env bash
exec "{python}" -m hupy hook {hook_name} "$@"
"""

_STUB_MODE = 0o755


# auxiliaries  #################################################################


def _write_stub(target_path, hook_name, is_overwrite=False, is_update=False):
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
    elif is_update:
        logger.info("hook stub added: {}".format(target_path))
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


def _begin_hooks_action(action_label, hooks_dir):
    """
    log entry into a ``hooks_dir``-scoped action and ensure the
    directory exists
    """
    logger.enter(action_label)
    logger.debug("hooks dir: {}".format(hooks_dir))

    hooks_dir.mkdir(parents=True, exist_ok=True)


def _install_or_abort(hooks_dir, hook_name, force):
    """
    write the stub for ``hook_name`` in ``hooks_dir``, aborting if one
    is already present unless ``force`` is set
    """
    target_path = hooks_dir / hook_name
    is_file_exist = target_path.exists()

    if is_file_exist and not force:
        logger.error(
            "hook already exists (use --force to override): {}".format(
                target_path
            )
        )
        raise SystemExit(1)

    _write_stub(target_path, hook_name, is_overwrite=is_file_exist)


def _report_hook_drift(hooks_dir, missing_names, unused_names):
    """
    warn about hook stubs demanded but not installed, and stubs
    installed but no longer demanded, without touching the file system
    """
    for hook_name in missing_names:
        logger.warning("missing hook stub: {}".format(hooks_dir / hook_name))

    for hook_name in unused_names:
        logger.warning(
            "hook stub no longer demanded: {}".format(hooks_dir / hook_name)
        )


def _remove_unused_stubs(hooks_dir, unused_names):
    """
    delete each no-longer-demanded stub in ``unused_names``
    """
    for hook_name in unused_names:
        target_path = hooks_dir / hook_name
        logger.warning("remove unused hook stub: {}".format(target_path))
        target_path.unlink()


def _add_missing_stubs(hooks_dir, missing_names):
    """
    write each demanded-but-missing stub in ``missing_names``
    """
    for hook_name in missing_names:
        _write_stub(hooks_dir / hook_name, hook_name, is_update=True)


def _uninstall_managed_stub(target_path, force):
    """
    delete ``target_path`` if ``force`` is set; otherwise only warn
    that it would be removed (dry run).
    """
    if force:
        logger.warning("remove hook stub: {}".format(target_path))
        target_path.unlink()
    else:
        logger.info("attempt remove stub: {}".format(target_path))


def _refresh_installed_stubs(hooks_dir, names):
    """
    regenerate every already-installed stub in ``names``
    """
    for hook_name in sorted(names):
        target_path = hooks_dir / hook_name
        _write_stub(target_path, hook_name, is_overwrite=True)


# Public API  ##################################################################


def resolve_hooks_dir(repo):
    """
    resolve ``repo``'s actual git hooks directory, honoring
    ``core.hooksPath`` if configured.


    :param repo: repo to resolve the hooks directory for
    :type repo: git.Repo
    :return: the repo's actual hooks directory
    :rtype: pathlib.Path
    """
    with repo.config_reader() as reader:
        configured = reader.get_value("core", "hooksPath", default="")

    if configured:
        return pathlib.Path(repo.working_tree_dir) / configured

    return pathlib.Path(repo.git_dir) / "hooks"


def install_hook_stubs(repo, hooks_dir=None, force=False):
    """
    create every hook stub demanded by ``get_hook_names_by_demand`` in
    ``repo``'s hooks dir, aborting on the first one already present
    unless ``force`` is set.


    :param repo: repo to check hook demand for and install stubs into
    :type repo: git.Repo
    :param hooks_dir: directory the hook stub scripts are created in;
            defaults to ``resolve_hooks_dir(repo)``
    :type hooks_dir: pathlib.Path, optional
    :param force: whether overwrite a hook stub already present in
            ``hooks_dir``
    :type force: bool, optional
    :raises SystemExit: a hook stub already exists in ``hooks_dir`` and
            ``force`` is ``False``
    """
    hooks_dir = hooks_dir or resolve_hooks_dir(repo)
    _begin_hooks_action("install hook stubs", hooks_dir)

    for hook_name in get_hook_names_by_demand(repo):
        _install_or_abort(hooks_dir, hook_name, force)


def uninstall_hook_stubs(repo, hooks_dir=None, force=False):
    """
    remove every HUPy-managed hook stub found in ``repo``'s hooks dir.

    a file only qualifies via ``_is_managed_stub``, so unrelated files
    sharing the hooks dir (eg git's own ``*.sample`` hooks, or
    hand-written hooks) are left untouched; nothing outside these
    matched files is ever removed.

    when ``force`` is not set, no file is deleted: each matching stub
    is only reported via a warning (dry run).


    :param repo: repo to uninstall hook stubs from
    :type repo: git.Repo
    :param hooks_dir: directory the hook stub scripts are searched in;
            defaults to ``resolve_hooks_dir(repo)``
    :type hooks_dir: pathlib.Path, optional
    :param force: whether actually delete matching stubs, rather than
            only reporting them
    :type force: bool, optional
    """
    hooks_dir = hooks_dir or resolve_hooks_dir(repo)
    logger.enter("uninstall hook stubs")
    logger.debug("hooks dir: {}".format(hooks_dir))

    if not hooks_dir.is_dir():
        return

    for target_path in sorted(hooks_dir.iterdir()):
        if _is_managed_stub(target_path):
            _uninstall_managed_stub(target_path, force)


def verify_hook_stubs(repo, hooks_dir=None, force=False, update=False):
    """
    verify ``repo``'s hooks dir is synced with the hook stubs demanded
    by ``get_hook_names_by_demand``.

    by default, the two are only compared and reported; when
    ``update`` is set, unused stubs are removed and missing ones are
    added, and, if ``force`` is also set, every already-installed
    demanded stub is regenerated.


    :param repo: repo to check hook demand for and verify stubs of
    :type repo: git.Repo
    :param hooks_dir: directory the hook stub scripts are verified in;
            defaults to ``resolve_hooks_dir(repo)``
    :type hooks_dir: pathlib.Path, optional
    :param force: whether also replace already-installed demanded
            stubs; requires ``update``
    :type force: bool, optional
    :param update: whether sync installed stubs to demand
    :type update: bool, optional
    """
    hooks_dir = hooks_dir or resolve_hooks_dir(repo)
    _begin_hooks_action("verify hook stubs", hooks_dir)

    demanded_set = set(get_hook_names_by_demand(repo))
    installed_set = {p.name for p in hooks_dir.iterdir() if _is_managed_stub(p)}

    missing_names = sorted(demanded_set - installed_set)
    unused_names = sorted(installed_set - demanded_set)

    if not update:
        _report_hook_drift(hooks_dir, missing_names, unused_names)
        return

    _remove_unused_stubs(hooks_dir, unused_names)
    _add_missing_stubs(hooks_dir, missing_names)

    if force:
        _refresh_installed_stubs(hooks_dir, demanded_set & installed_set)
