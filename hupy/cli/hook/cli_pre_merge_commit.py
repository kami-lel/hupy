"""
cli_pre_merge_commit.py

define ``register_cli_pre_merge_commit_parser``, the pre-merge-commit
hook subcommand
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + ".pre-merge-commit")
logger.propagate = False

# constants  ###################################################################
_PRE_MERGE_COMMIT_DOC = "run pre-merge-commit stage hooks"


def _pre_merge_commit_main(args):  #############################################
    """
    dispatch for the ``pre-merge-commit`` subcommand
    """
    logger.enter("Start")
    logger.debug("No Operation in this HUPy version")
    logger.succ("Finished")


# Public API  ##################################################################
def register_cli_pre_merge_commit_parser(subparser):
    """
    register the ``pre-merge-commit`` subcommand parser.
    """
    pre_merge_commit_parser = subparser.add_parser(
        "pre-merge-commit",
        help=_PRE_MERGE_COMMIT_DOC,
        description=_PRE_MERGE_COMMIT_DOC,
    )
    pre_merge_commit_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(pre_merge_commit_parser)
    pre_merge_commit_parser.set_defaults(func=_pre_merge_commit_main)
