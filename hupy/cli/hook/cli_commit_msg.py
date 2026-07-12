"""
cli_commit_msg.py

define ``register_cli_commit_msg_parser``, the commit-msg hook subcommand
"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.cli.hook import HOOK_STAGE_FINISHED, HOOK_STAGE_NOOP, HOOK_STAGE_START
from hupy.state.open_state import open_state_file

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + ".commit-msg")
logger.propagate = False

# constants  ###################################################################
_COMMIT_MSG_DOC = "run commit-msg stage hooks"


def _commit_msg_main(args):  ###################################################
    """
    dispatch for the ``commit-msg`` subcommand
    """
    repo = load_git_repo(os.getcwd())

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )
        logger.enter(HOOK_STAGE_START)
        logger.debug(HOOK_STAGE_NOOP)
        logger.succ(HOOK_STAGE_FINISHED)


# Public API  ##################################################################
def register_cli_commit_msg_parser(subparser):
    """
    register the ``commit-msg`` subcommand parser.
    """
    commit_msg_parser = subparser.add_parser(
        "commit-msg",
        help=_COMMIT_MSG_DOC,
        description=_COMMIT_MSG_DOC,
    )
    commit_msg_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(commit_msg_parser)
    commit_msg_parser.set_defaults(func=_commit_msg_main)
