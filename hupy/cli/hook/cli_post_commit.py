"""post-commit stage hook runner for HUPy"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.state.open_state import open_state_file

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME)

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
        logger.enter("start post-commit stage")

        perform_hook_brackets(repo, state_file, "post-commit", True)

        perform_hook_brackets(repo, state_file, "post-commit", False)

        state_file.reset_for_next_commit()

        logger.succ("post-commit stage finished")
        logger.done("all HUPy hooks finished")


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
    kamilog.add_verbose_arguments(post_commit_parser)
    post_commit_parser.set_defaults(func=_post_commit_main)
