"""pre-commit stage hook runner for HUPy"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.state.open_state import open_state_file
from hupy.ttg.gate_tt import perform_triage_tags_gating
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
    repo = load_git_repo(os.getcwd())

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )

        logger.enter("start pre-commit stage")

        perform_hook_brackets(repo, state_file, "pre-commit", True)
        ban_direct_commit(repo, state_file)
        perform_triage_tags_gating(repo, state_file)
        perform_hook_brackets(repo, state_file, "pre-commit", False)

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
