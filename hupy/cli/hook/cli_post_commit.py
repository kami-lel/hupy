"""
cli_post_commit.py

define ``register_cli_post_commit_parser``, the post-commit hook subcommand
"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.cli.hook import HOOK_STAGE_FINISHED, HOOK_STAGE_START
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.state.open_state import open_state_file

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + ".post-commit")
logger.propagate = False
proj_root_logger = kamilog.getLogger(PROJ_LOGGER_NAME)


# constants  ###################################################################
_POST_COMMIT_DOC = "run post-commit stage hooks"


def _post_commit_main(args):  ##################################################
    """
    dispatch for the ``post-commit`` subcommand: reset one-time state
    for the next commit.
    """
    repo = load_git_repo(os.getcwd())

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )
        logger.enter(HOOK_STAGE_START)

        perform_hook_brackets(
            repo, state_file, "post-commit", True, args.hook_args
        )

        perform_hook_brackets(
            repo, state_file, "post-commit", False, args.hook_args
        )

        state_file.reset_for_next_commit()

        logger.succ(HOOK_STAGE_FINISHED)
        proj_root_logger.done("all HUPy hooks finished")


# Public API  ##################################################################
def register_cli_post_commit_parser(subparser):
    """
    register the ``post-commit`` subcommand parser.
    """
    post_commit_parser = subparser.add_parser(
        "post-commit",
        help=_POST_COMMIT_DOC,
        description=_POST_COMMIT_DOC,
    )
    post_commit_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(post_commit_parser)
    post_commit_parser.set_defaults(func=_post_commit_main)
