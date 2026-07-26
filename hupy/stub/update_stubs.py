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


def _render_stub_content(hook_name):
    """
    render the stub script content for ``hook_name``, with the running
    interpreter's path baked in
    """
    return _STUB_TEMPLATE.format(python=sys.executable, hook_name=hook_name)


def _write_stub(target_path, hook_name, is_overwrite=False, is_update=False):
    """
    render and write the stub script for ``hook_name`` at ``target_path``,
    then mark it executable.
    """
    target_path.write_text(_render_stub_content(hook_name), encoding="utf-8")
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
    ``*.sample`` hooks) sharing the hooks dir
    """
    if not target_path.is_file():
        return False

    try:
        content = target_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    return "-m hupy hook {}".format(target_path.name) in content


def _is_stub_current(target_path, hook_name):
    """
    report whether the installed stub at ``target_path`` matches what
    HUPy renders today for ``hook_name``; a mismatch means a drifted
    stub — hand-edited, or left behind by an interpreter that has
    since moved
    """
    try:
        content = target_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    return content == _render_stub_content(hook_name)


def _diff_hook_stubs(repo, hooks_dir):
    """
    diff demanded hook names against the HUPy-managed stubs present in
    ``hooks_dir``, without touching the file system; returns sorted
    missing, stale, and unused hook names as a 3-tuple of lists
    """
    demanded_set = set(get_hook_names_by_demand(repo))

    if hooks_dir.is_dir():
        installed_set = {
            p.name for p in hooks_dir.iterdir() if _is_managed_stub(p)
        }
    else:
        installed_set = set()

    stale_names = [
        hook_name
        for hook_name in sorted(demanded_set & installed_set)
        if not _is_stub_current(hooks_dir / hook_name, hook_name)
    ]

    return (
        sorted(demanded_set - installed_set),
        stale_names,
        sorted(installed_set - demanded_set),
    )


def _begin_hooks_action(action_label, hooks_dir, is_dry_run=False):
    """
    log entry into a ``hooks_dir``-scoped action and ensure the
    directory exists; a dry run creates nothing
    """
    logger.enter(action_label)
    logger.debug("hooks dir: {}".format(hooks_dir))

    if is_dry_run:
        logger.note("dry run: no file is written or removed")
        return

    hooks_dir.mkdir(parents=True, exist_ok=True)


def _remove_unused_stubs(hooks_dir, unused_names, is_dry_run=False):
    """
    delete each no-longer-demanded stub in ``unused_names``
    """
    for hook_name in unused_names:
        target_path = hooks_dir / hook_name

        if is_dry_run:
            logger.info("would remove unused stub: {}".format(target_path))
            continue

        logger.warning("remove unused hook stub: {}".format(target_path))
        target_path.unlink()


def _report_unused_stubs(hooks_dir, unused_names):
    """
    warn about installed stubs no longer demanded, left in place
    because pruning was not asked for
    """
    for hook_name in unused_names:
        logger.warning(
            "hook stub no longer demanded, use --prune to remove: "
            "{}".format(hooks_dir / hook_name)
        )


def _add_missing_stubs(hooks_dir, missing_names, is_dry_run=False):
    """
    write each demanded-but-missing stub in ``missing_names``
    """
    for hook_name in missing_names:
        target_path = hooks_dir / hook_name

        if is_dry_run:
            logger.info("would add hook stub: {}".format(target_path))
            continue

        _write_stub(target_path, hook_name, is_update=True)


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


def _refresh_stale_stubs(hooks_dir, stale_names, is_dry_run=False):
    """
    regenerate every drifted stub in ``stale_names``
    """
    for hook_name in stale_names:
        target_path = hooks_dir / hook_name

        if is_dry_run:
            logger.info("would rewrite stale stub: {}".format(target_path))
            continue

        _write_stub(target_path, hook_name, is_overwrite=True)


def _report_stale_stubs(hooks_dir, stale_names):
    """
    warn about drifted stubs left in place because overriding was not
    asked for
    """
    for hook_name in stale_names:
        logger.warning(
            "hook stub differs from what HUPy renders, use --force to "
            "rewrite: {}".format(hooks_dir / hook_name)
        )


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


def sync_hook_stubs(
    repo, hooks_dir=None, force=False, prune=False, dry_run=False
):
    """
    converge ``repo``'s hooks dir onto the stubs demanded by
    ``get_hook_names_by_demand``.

    demanded-but-missing stubs are always written. a stub already
    present and matching what HUPy renders is left alone, so repeat
    runs are silent; one that has drifted is only rewritten under
    ``force``, and one no longer demanded is only removed under
    ``prune`` — both are reported otherwise. ``dry_run`` reports every
    intended action and touches nothing.


    :param repo: repo to check hook demand for and install stubs into
    :type repo: git.Repo
    :param hooks_dir: directory the hook stub scripts are created in;
            defaults to ``resolve_hooks_dir(repo)``
    :type hooks_dir: pathlib.Path, optional
    :param force: whether rewrite installed stubs that have drifted
    :type force: bool, optional
    :param prune: whether remove installed stubs no longer demanded
    :type prune: bool, optional
    :param dry_run: whether report intended actions without writing
    :type dry_run: bool, optional
    """
    hooks_dir = hooks_dir or resolve_hooks_dir(repo)
    _begin_hooks_action("sync hook stubs", hooks_dir, is_dry_run=dry_run)

    missing_names, stale_names, unused_names = _diff_hook_stubs(
        repo, hooks_dir
    )

    _add_missing_stubs(hooks_dir, missing_names, is_dry_run=dry_run)

    if force:
        _refresh_stale_stubs(hooks_dir, stale_names, is_dry_run=dry_run)
    else:
        _report_stale_stubs(hooks_dir, stale_names)

    if prune:
        _remove_unused_stubs(hooks_dir, unused_names, is_dry_run=dry_run)
    else:
        _report_unused_stubs(hooks_dir, unused_names)


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
        logger.error("hooks dir does not exist: {}".format(hooks_dir))
        return

    for target_path in sorted(hooks_dir.iterdir()):
        if _is_managed_stub(target_path):
            _uninstall_managed_stub(target_path, force)


def check_hook_stubs(repo, hooks_dir=None):
    """
    compare ``repo``'s hooks dir against the stubs demanded by
    ``get_hook_names_by_demand``, purely by reading.

    nothing is created, written, or removed — not even the hooks
    directory itself, which is reported as fully missing when absent.


    :param repo: repo to check hook demand for and check stubs of
    :type repo: git.Repo
    :param hooks_dir: directory the hook stub scripts are checked in;
            defaults to ``resolve_hooks_dir(repo)``
    :type hooks_dir: pathlib.Path, optional
    :return: sorted demanded-but-missing, drifted, and no-longer-
            demanded hook names
    :rtype: tuple[list[str], list[str], list[str]]
    """
    hooks_dir = hooks_dir or resolve_hooks_dir(repo)

    logger.enter("check hook stubs")
    logger.debug("hooks dir: {}".format(hooks_dir))

    return _diff_hook_stubs(repo, hooks_dir)
