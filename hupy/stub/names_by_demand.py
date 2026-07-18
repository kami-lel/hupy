"""
names_by_demand.py

decide which git hook names actually need an installed stub
"""

import importlib
import pkgutil

import hupy.cli.hooks as _hook_pkg
from hupy.config_file.load_config import load_hupy_config
from hupy.kamilog import getLogger
from hupy.stub import STUB_LOGGER_NAME

__all__ = ("get_hook_names_by_demand",)


# logger  ######################################################################

logger = getLogger(STUB_LOGGER_NAME)
logger.propagate = False


# auxiliaries  #################################################################
def _iter_hook_stage_modules():
    """
    :return: every hook stage module living under ``hupy.cli.hooks``
    :rtype: collections.abc.Iterator[module]
    """
    for info in pkgutil.iter_modules(_hook_pkg.__path__):
        mod = importlib.import_module("hupy.cli.hooks.{}".format(info.name))
        if hasattr(mod, "HOOK_NAME"):
            yield mod


def _is_hb_bracket_active(config, hook_name):
    """
    :param config: loaded HUPy config, or ``None`` when unset
    :type config: HupyConfigFile or None
    :param hook_name: hook name, eg ``"pre-commit"``
    :type hook_name: str
    :return: whether HB is enabled and the hook's bracket holds any
            command
    :rtype: bool
    """
    if config is None or config.hb.is_disabled:
        return False

    bracket = config.hb.get_bracket(hook_name)
    return bracket is not None and bracket.should_install_hook_stub()


def _is_demanded(mod, config):
    """
    :param mod: hook stage module to check
    :type mod: module
    :param config: loaded HUPy config, or ``None`` when unset
    :type config: HupyConfigFile or None
    :return: whether ``mod``'s hook needs an installed stub
    :rtype: bool
    """
    return (
        _is_hb_bracket_active(config, mod.HOOK_NAME)
        or hasattr(mod, "run_features")
        or hasattr(mod, "run_after")
    )


# Public API  ##################################################################
def get_hook_names_by_demand(repo):
    """
    :param repo: repo to check hook demand for
    :type repo: git.Repo
    :return: hook names that should have an installed stub
    :rtype: list[str]
    """
    config = load_hupy_config(repo, allows_file_not_found=True)

    names = [
        mod.HOOK_NAME
        for mod in _iter_hook_stage_modules()
        if _is_demanded(mod, config)
    ]

    logger.debug("demanded hook names:\n{}".format(", ".join(names)))
    return names
