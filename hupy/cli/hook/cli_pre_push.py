"""
cli_pre_push.py

define ``register_cli_pre_push_parser``, the pre-push hook subcommand
"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.cli.hook import HOOK_STAGE_FINISHED, HOOK_STAGE_NOOP, HOOK_STAGE_START
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.state.open_state import open_state_file

# constants  ###################################################################
_HOOK_NAME = "pre-push"
_PRE_PUSH_DOC = "run pre-push stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + _HOOK_NAME)
logger.propagate = False


def _pre_push_main(args):  #####################################################
    """
    dispatch for the ``pre-push`` subcommand
    """
    repo = load_git_repo(os.getcwd())

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )
        logger.enter(HOOK_STAGE_START)

        perform_hook_brackets(
            repo, state_file, _HOOK_NAME, True, args.hook_args
        )

        logger.debug(HOOK_STAGE_NOOP)

        perform_hook_brackets(
            repo, state_file, _HOOK_NAME, False, args.hook_args
        )

        logger.succ(HOOK_STAGE_FINISHED)


# Public API  ##################################################################
def register_cli_pre_push_parser(subparser):
    """
    register the ``pre-push`` subcommand parser.
    """
    pre_push_parser = subparser.add_parser(
        _HOOK_NAME,
        help=_PRE_PUSH_DOC,
        description=_PRE_PUSH_DOC,
    )
    pre_push_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(pre_push_parser)
    pre_push_parser.set_defaults(func=_pre_push_main)
