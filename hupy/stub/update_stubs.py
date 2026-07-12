"""
update_stubs.py

dynamically generate & write git hook stub scripts into a repo's
hooks directory: content is rendered in-process from each registered
hook stage's ``HOOK_NAME``, no on-disk template files or placeholder
substitution involved
"""

import importlib
import pkgutil
import sys

from hupy.cli import hook as _hook_pkg
from hupy.kamilog import getLogger
from hupy.stub import STUB_LOGGER_NAME

# logger  ######################################################################

logger = getLogger(STUB_LOGGER_NAME)
logger.propagate = False

# constants  ###################################################################

_STUB_TEMPLATE = '#!/usr/bin/env bash\n"{python}" -m hupy hook {hook_name} "$@"\n'

_STUB_MODE = 0o755


# auxiliaries  #################################################################


def _iter_hook_names():
    """
    yield every registered git hook stage name, sourced from each hook
    stage module's ``HOOK_NAME`` (keeps stub generation in sync with
    ``cli_hook.py`` without a second, hand-maintained list)
    """
    for _finder, module_name, _is_pkg in pkgutil.iter_modules(
        _hook_pkg.__path__
    ):
        if module_name == "cli_hook":
            continue

        module = importlib.import_module(
            "{}.{}".format(_hook_pkg.__name__, module_name)
        )
        hook_name = getattr(module, "HOOK_NAME", None)
        if hook_name is not None:
            yield hook_name


def _render_stub(hook_name):
    """render one hook stub script's content, baking in ``sys.executable``."""
    return _STUB_TEMPLATE.format(python=sys.executable, hook_name=hook_name)


# Public API  ##################################################################


def update_hooks_stub(hooks_dir, force=False):
    """
    dynamically generate and write every HUPy hook stub script into
    ``hooks_dir``.


    :param hooks_dir: directory the hook stub scripts are written into
    :type hooks_dir: pathlib.Path
    :param force: whether overwrite a hook stub already present in ``hooks_dir``
    :type force: bool, optional
    :raises SystemExit: a hook stub already exists in ``hooks_dir`` and
            ``force`` is ``False``
    """
    logger.enter("update hook stubs")
    hooks_dir.mkdir(parents=True, exist_ok=True)

    for hook_name in sorted(_iter_hook_names()):
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

        target_path.write_text(_render_stub(hook_name), encoding="utf-8")
        target_path.chmod(_STUB_MODE)

        logger.debug("hook stub installed: {}".format(target_path))
