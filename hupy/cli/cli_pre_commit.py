"""pre-commit stage hook runner for HUPy"""

import os

import git

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.config.load_config import load_hupy_config
from hupy.ttg.tt_gating import perform_triage_tags_gating
from hupy.bdc.ban_direct_commit import ban_direct_commit

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME)

# constants  ###################################################################
_PRE_COMMIT_DOC = "run pre-commit stage hooks"


def _pre_commit_main(args):  ###################################################
    """
    dispatch for the ``pre-commit`` subcommand: execute direct-commit
    ban and triage tag gating.
    """
    repo = git.Repo(os.getcwd(), search_parent_directories=True)
    config = load_hupy_config(repo)
    kamilog.set_logging_level_by_namespace(
        args, verbosity=config.default_logger_verbosity
    )

    logger.enter("start pre-commit stage")

    ban_direct_commit(repo)
    perform_triage_tags_gating(repo)

    logger.succ("pre-commit stage finished")


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
