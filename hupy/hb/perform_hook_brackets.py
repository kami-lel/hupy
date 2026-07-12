"""
perform_hook_brackets.py

run the bracketed commands configured around a HUPy git hook
"""

import os
import shlex
import subprocess
import sys


from hupy.kamilog import (
    AnsiRenderer,
    AnsiStyle,
    getLogger,
    gen_comment_banner_centered,
)
from hupy.cbm.get_current_commit_type import get_current_commit_type
from hupy.config_file.load_config import load_hupy_config
from hupy.should_run_module import should_run_module
from . import HB_LOGGER_NAME

# logger  ######################################################################
logger = getLogger(HB_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

_renderer = AnsiRenderer(sys.stdout)

_OPT_HEADING = "OUTPUT"

_START_LINE = gen_comment_banner_centered(_OPT_HEADING, "v", renderer=_renderer)

_END_LINE = gen_comment_banner_centered(
    _OPT_HEADING, "^", line_width=58, horizontal_offset=-11, renderer=_renderer
)


# auxiliaries  #################################################################
def _is_hb_cmd_applicable(hb_cmd, commit_type):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :param hb_cmd:
    :type hb_cmd: _HbCmd
    :return: if ``hb_cmd`` should run for the current commit type
    :rtype: bool
    """
    if not hb_cmd.allow_commit_types:
        return True  # no filter configured, always applicable

    logger.debug("allow commit types: {}".format(hb_cmd.allow_commit_types))

    return bool(hb_cmd.allow_commit_types & commit_type)


def _run_hb_cmd(repo, heading, hb_cmd, hooks_args):
    """
    :param repo: git repository object
    :type repo: git.Repo
    :param hb_cmd: a single bracketed command
    :type hb_cmd: _HbCmd
    :param hooks_args: raw arguments forwarded by the git hook invocation
    :type hooks_args: list[str]
    """
    logger.info("run HB: {}".format(heading))
    cmd = " ".join([hb_cmd.cmd, *(shlex.quote(arg) for arg in hooks_args)])
    logger.debug("command:\n{}\n{}".format(cmd, _START_LINE))

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=repo.working_tree_dir,
            check=False,
            executable="/bin/bash",
            env=os.environ.copy(),
            timeout=hb_cmd.timeout,
        )
    except subprocess.TimeoutExpired as e:
        logger.debug(_END_LINE)

        if hb_cmd.allow_failure:
            logger.warning("HB timed out, but ignored: {}".format(heading))
            return

        logger.fail("HB timed out: {}".format(heading))
        raise SystemExit(1) from e

    logger.debug(_END_LINE)

    if result.returncode == 0:
        logger.pass_("HB succeeded: {}".format(heading))

    elif hb_cmd.allow_failure:
        logger.warning("HB failed, but ignored: {}".format(heading))

    else:
        logger.fail("HB failed: {}".format(heading))
        raise SystemExit(result.returncode)


# Public API  ##################################################################
def perform_hook_brackets(repo, state_file, hook_name, is_lead, hooks_args=()):
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
    :param hooks_args: raw arguments forwarded by the git hook invocation
    :type hooks_args: list[str], optional
    """
    if not should_run_module(repo, state_file, "hb"):
        return

    lead_trail = "Lead" if is_lead else "Trail"
    logger.enter("{} HB for: {}".format(lead_trail, hook_name))

    bracket = load_hupy_config(repo).hb.get_bracket(hook_name)
    if bracket is None:
        raise ValueError("unrecognized hook name: {}".format(hook_name))

    cmds_list = bracket.lead if is_lead else bracket.trail

    # empty commands list
    if not cmds_list:
        logger.skip("no {} HB".format(lead_trail))
        return

    commit_type = get_current_commit_type(repo)

    for hb_cmd in cmds_list:
        heading = hb_cmd.remark or _renderer.color(
            hb_cmd.cmd, AnsiStyle.UNDERLINE
        )
        logger.enter("HB subroutine: " + heading)

        if not _is_hb_cmd_applicable(hb_cmd, commit_type):
            logger.skip("due to commit type filtered: {}".format(heading))
            continue

        _run_hb_cmd(repo, heading, hb_cmd, hooks_args)
