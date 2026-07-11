"""
perform_hook_brackets.py

run the bracketed commands configured around a HUPy git hook
"""

import subprocess

from hupy.cbm import get_current_commit_type
from hupy.config.load_config import load_hupy_config
from hupy.kamilog import getLogger
from hupy.should_run_module import should_run_module
from . import HB_LOGGER_NAME

# logger  ######################################################################
logger = getLogger(HB_LOGGER_NAME)
logger.propagate = False


# helpers  #####################################################################


def _is_hb_cmd_applicable(repo, hb_cmd):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :param hb_cmd: a single bracketed command
    :type hb_cmd: _HbCmd
    :return: if ``hb_cmd`` should run for the current commit type
    :rtype: bool
    """
    if not hb_cmd.commit_types:
        return True

    return get_current_commit_type(repo).name in hb_cmd.commit_types


def _run_hb_cmd(repo, hb_cmd):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :param hb_cmd: a single bracketed command
    :type hb_cmd: _HbCmd
    """
    logger.enter("run bracketed command: {}".format(hb_cmd.cmd))

    result = subprocess.run(hb_cmd.cmd, shell=True, cwd=repo.working_tree_dir)

    if result.returncode == 0:
        logger.pass_("bracketed command succeeded: {}".format(hb_cmd.cmd))
        return

    if hb_cmd.allow_failure:
        logger.warning(
            "bracketed command failed, ignored: {}".format(hb_cmd.cmd)
        )
        return

    logger.fail("bracketed command failed: {}".format(hb_cmd.cmd))
    raise SystemExit(result.returncode)


# TODO fuller set of UT
# Public API  ##################################################################
def perform_hook_brackets(repo, state_file, hook_name, is_lead):
    """
    run the lead or trail bracketed commands configured for
    ``hook_name``.

    :param repo: git repository object
    :type repo: git.Repo
    :param state_file: the open HUPy state file, as yielded by
            ``open_state_file``
    :type state_file: HupyStateFile
    :param hook_name: hook name, eg ``"pre-commit"``
    :type hook_name: str
    :param is_lead: if ``True``, run the bracket's ``lead`` commands;
            otherwise run its ``trail`` commands
    :type is_lead: bool
    """
    if not should_run_module(repo, state_file, "hb"):
        return

    lead_trail = "Leading" if is_lead else "Trailing"
    logger.enter("{} Hook Bracket for: {}".format(lead_trail, hook_name))

    bracket = load_hupy_config(repo).hb.get_bracket(hook_name)
    if bracket is None:
        raise ValueError("unrecognized hook name: {}".format(hook_name))

    cmds_list = bracket.lead if is_lead else bracket.trail

    # empty commands list
    if not cmds_list:
        logger.skip(
            "no {} bracket commands for: {}".format(lead_trail, hook_name)
        )
        return

    # BUG commit type filtering is wrong

    # HACK write better interactions
    for hb_cmd in cmds_list:
        if not _is_hb_cmd_applicable(repo, hb_cmd):
            logger.skip("commit type mismatch, skipped: {}".format(hb_cmd.cmd))
            continue

        _run_hb_cmd(repo, hb_cmd)
