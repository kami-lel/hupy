"""
names_by_demand.py

decide which git hook names actually need an installed stub
"""

import importlib
import pkgutil

import hupy.cli.hook as _hook_pkg
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
    :return: every hook stage module living under ``hupy.cli.hook``
    :rtype: collections.abc.Iterator[module]
    """
    for info in pkgutil.iter_modules(_hook_pkg.__path__):
        mod = importlib.import_module("hupy.cli.hook.{}".format(info.name))
        if hasattr(mod, "HOOK_NAME"):
            yield mod


def _has_hb_commands(config, hook_name):
    """
    :param config: loaded HUPy config
    :type config: HupyConfigFile
    :param hook_name: hook name, eg ``"pre-commit"``
    :type hook_name: str
    :return: whether the hook's HB bracket holds any command
    :rtype: bool
    """
    bracket = config.hb.get_bracket(hook_name)
    return bracket is not None and bracket.should_install_hook_stub()


def _is_demanded(mod, config):
    """
    :param mod: hook stage module to check
    :type mod: module
    :param config: loaded HUPy config
    :type config: HupyConfigFile
    :return: whether ``mod``'s hook needs an installed stub
    :rtype: bool
    """
    return (
        _has_hb_commands(config, mod.HOOK_NAME)
        or hasattr(mod, "run_core")
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
    config = load_hupy_config(repo)

    names = [
        mod.HOOK_NAME
        for mod in _iter_hook_stage_modules()
        if _is_demanded(mod, config)
    ]

    logger.debug("demanded hook names:\n{}".format(", ".join(names)))
    return names
