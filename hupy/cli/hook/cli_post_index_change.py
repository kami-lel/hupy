"""
cli_post_index_change.py

define ``register_cli_post_index_change_parser``, the post-index-change
hook subcommand
"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.cli.hook import HOOK_STAGE_FINISHED, HOOK_STAGE_NOOP, HOOK_STAGE_START
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.state.open_state import open_state_file

# constants  ###################################################################
_HOOK_NAME = "post-index-change"
_POST_INDEX_CHANGE_DOC = "run post-index-change stage hooks"

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + _HOOK_NAME)
logger.propagate = False


def _post_index_change_main(args):  ############################################
    """
    dispatch for the ``post-index-change`` subcommand
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
def register_cli_post_index_change_parser(subparser):
    """
    register the ``post-index-change`` subcommand parser.
    """
    post_index_change_parser = subparser.add_parser(
        _HOOK_NAME,
        help=_POST_INDEX_CHANGE_DOC,
        description=_POST_INDEX_CHANGE_DOC,
    )
    post_index_change_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(post_index_change_parser)
    post_index_change_parser.set_defaults(func=_post_index_change_main)
