"""
should_run_module.py

decide whether a HUPy module should run this hook invocation,
combining its config ``is_disabled`` flag with the state file's
one-time ``skip_once`` set
"""

from hupy import PROJ_LOGGER_NAME
from hupy.config.load_config import load_hupy_config
from hupy.kamilog import getLogger

__all__ = ("should_run_module",)

# logger  ######################################################################

logger = getLogger(PROJ_LOGGER_NAME)
logger.propagate = False

# constants  ###################################################################

_MODULE_ABBR_TO_NAME = {
    "vg": "VerGrep",
    "ttg": "Triage Tag Gating",
    "pch": "Prepend Commit Header",
    "bdc": "Ban Direct Commit",
    "hb": "Hook Bracket",
}


# Public API  ##################################################################
def should_run_module(repo, state_file, module_abbr):
    """
    decide whether ``module_abbr`` should run for this hook
    invocation; consumes a matching ``skip_once`` entry from
    ``state_file`` if present.


    :param repo: git repository object
    :type repo: git.Repo
    :param state_file: the open HUPy state file, as yielded by
            ``open_state_file``
    :type state_file: HupyStateFile
    :param module_abbr: module abbreviation, eg ``"bdc"``
    :type module_abbr: str
    :return: ``True`` if the module should run this invocation
    :rtype: bool
    """
    module_name = _MODULE_ABBR_TO_NAME[module_abbr]

    config = load_hupy_config(repo)
    if getattr(config, module_abbr).is_disabled:
        logger.skip("{} disabled in config file".format(module_name))
        return False

    if module_abbr in state_file.skip_once:
        logger.skip("{} skipped once".format(module_name))
        return False

    return True
