"""prepare-commit-msg stage hook runner for HUPy"""

import os

import git

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.pch.prepend_commit_header import prepend_commit_header
from hupy.state.open_state import open_state_file

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME)

# constants  ###################################################################

_PREPARE_COMMIT_MSG_DOC = "run prepare-commit-msg stage hooks"


def _prepare_commit_msg_main(args):  ###########################################
    """
    dispatch for the ``prepare-commit-msg`` subcommand: execute prepend
    commit header.
    """
    repo = git.Repo(os.getcwd(), search_parent_directories=True)

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.logger_verbosity
        )

        logger.enter("start prepare-commit-msg stage")

        perform_hook_brackets(repo, state_file, "prepare-commit-msg", True)
        prepend_commit_header(repo, state_file)
        perform_hook_brackets(repo, state_file, "prepare-commit-msg", False)

        state_file.reset_for_next_commit()

        logger.succ("prepare-commit-msg stage finished")
        logger.done("all HUPy hooks finished")


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
    kamilog.add_verbose_arguments(prepare_commit_msg_parser)
    prepare_commit_msg_parser.set_defaults(func=_prepare_commit_msg_main)
