"""prepare-commit-msg stage hook runner for HUPy"""

import os

import git

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.config.load_config import load_hupy_config
from hupy.pch.prepend_commit_header import prepend_commit_header

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
    config = load_hupy_config(os.getcwd())
    kamilog.set_logging_level_by_namespace(
        args, verbosity=config.default_logger_verbosity
    )

    logger.enter("Start prepare-commit-msg stage")

    prepend_commit_header(repo)

    logger.succ("prepare-commit-msg HUPy hooks")
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
