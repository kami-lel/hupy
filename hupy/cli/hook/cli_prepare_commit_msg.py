"""prepare-commit-msg stage hook runner for HUPy"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.pch.prepend_commit_header import prepend_commit_header
from hupy.state.open_state import open_state_file

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + ".prepare-commit-msg")
logger.propagate = False

# constants  ###################################################################

_PREPARE_COMMIT_MSG_DOC = "run prepare-commit-msg stage hooks"


def _prepare_commit_msg_main(args):  ###########################################
    """
    dispatch for the ``prepare-commit-msg`` subcommand: execute prepend
    commit header.
    """
    repo = load_git_repo(os.getcwd())

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )

        logger.enter("Start")

        perform_hook_brackets(
            repo, state_file, "prepare-commit-msg", True, args.hook_args
        )
        prepend_commit_header(repo, state_file)
        perform_hook_brackets(
            repo, state_file, "prepare-commit-msg", False, args.hook_args
        )

        logger.succ("Finished")


# Public API  ##################################################################
def register_cli_prepare_commit_msg_parser(subparser):
    """
    register the ``prepare-commit-msg`` subcommand parser.
    """
    prepare_commit_msg_parser = subparser.add_parser(
        "prepare-commit-msg",
        help=_PREPARE_COMMIT_MSG_DOC,
        description=_PREPARE_COMMIT_MSG_DOC,
    )
    prepare_commit_msg_parser.add_argument(
        "hook_args",
        metavar="ARG",
        nargs="*",
        help="raw arguments forwarded by the git hook invocation",
    )
    kamilog.add_verbose_arguments(prepare_commit_msg_parser)
    prepare_commit_msg_parser.set_defaults(func=_prepare_commit_msg_main)
