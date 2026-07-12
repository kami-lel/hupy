"""
cli_commit_msg.py

define ``register_cli_commit_msg_parser``, the commit-msg hook subcommand
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + ".commit-msg")
logger.propagate = False

# constants  ###################################################################
_COMMIT_MSG_DOC = "run commit-msg stage hooks"


def _commit_msg_main(args):  ###################################################
    """
    dispatch for the ``commit-msg`` subcommand
    """
    logger.enter("Start")
    logger.debug("No Operation in this HUPy version")
    logger.succ("Finished")


# Public API  ##################################################################
def register_cli_commit_msg_parser(subparser):
    """
    register the ``commit-msg`` subcommand parser.
    """
    commit_msg_parser = subparser.add_parser(
        "commit-msg",
        help=_COMMIT_MSG_DOC,
        description=_COMMIT_MSG_DOC,
    )
    commit_msg_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(commit_msg_parser)
    commit_msg_parser.set_defaults(func=_commit_msg_main)
