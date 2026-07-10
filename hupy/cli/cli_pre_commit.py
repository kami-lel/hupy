"""pre-commit stage hook runner for HUPy"""

import os

import git

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.config.load_config import load_hupy_config
from hupy.ttg.tt_gating import perform_triage_tags_gating

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME)

# constants  ###################################################################
_PRE_COMMIT_DOC = "run pre-commit stage hooks"


def _pre_commit_main(args):  ###################################################
    """
    dispatch for the ``pre-commit`` subcommand: execute triage tag gating.
    """
    repo = git.Repo(os.getcwd(), search_parent_directories=True)
    config = load_hupy_config(os.getcwd())
    kamilog.set_logging_level_by_namespace(
        args, verbosity=config.default_logger_verbosity
    )

    logger.enter("Start pre-commit stage")

    perform_triage_tags_gating(repo)

    logger.succ("pre-commit HUPy hooks")


# Public API  ##################################################################
def register_cli_pre_commit_parser(subparser):
    """
    register the ``pre-commit`` subcommand parser.
    """
    pre_commit_parser = subparser.add_parser(
        "pre-commit",
        help=_PRE_COMMIT_DOC,
        description=_PRE_COMMIT_DOC,
    )
    kamilog.add_verbose_arguments(pre_commit_parser)
    pre_commit_parser.set_defaults(func=_pre_commit_main)
