"""
cli_post_rewrite.py

define ``register_cli_post_rewrite_parser``, the post-rewrite hook
subcommand
"""

from hupy import PROJ_LOGGER_NAME, kamilog

# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME + ".post-rewrite")
logger.propagate = False

# constants  ###################################################################
_POST_REWRITE_DOC = "run post-rewrite stage hooks"


def _post_rewrite_main(args):  #################################################
    """
    dispatch for the ``post-rewrite`` subcommand
    """
    logger.enter("Start")
    logger.debug("No Operation in this HUPy version")
    logger.succ("Finished")


# Public API  ##################################################################
def register_cli_post_rewrite_parser(subparser):
    """
    register the ``post-rewrite`` subcommand parser.
    """
    post_rewrite_parser = subparser.add_parser(
        "post-rewrite",
        help=_POST_REWRITE_DOC,
        description=_POST_REWRITE_DOC,
    )
    post_rewrite_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(post_rewrite_parser)
    post_rewrite_parser.set_defaults(func=_post_rewrite_main)
