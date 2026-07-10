"""flag HUPy modules to be skipped once on their next hook run"""

import argparse
import os

import git

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)
from hupy.state.open_state import open_state_file

# logger  ######################################################################

SKIP_ONCE_LOGGER_NAME = PROJ_LOGGER_NAME + ".skip_once"

logger = getLogger(SKIP_ONCE_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

SKIPPABLE_MODULES = ("ver_grep", "ttg", "pch", "bdc", "hb")

_SKIP_ONCE_DOC = "skip modules in next hook run"

_DESCRIPTION = __doc__ + """

modules: {}

each flagged module is skipped exactly once, consumed by the next
pre-commit/prepare-commit-msg run that checks it, regardless of its
is_disabled config setting
""".format(", ".join(SKIPPABLE_MODULES))


# helpers  #####################################################################


def _skip_once_main(args):
    """
    dispatch for the ``skip-once`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args, logger=logger)

    repo = git.Repo(os.getcwd(), search_parent_directories=True)

    with open_state_file(repo) as state_file:
        for module in args.modules:
            if module not in state_file.skip_once:
                state_file.skip_once.append(module)

        logger.done(
            "flagged for one-time skip: {}".format(", ".join(args.modules))
        )


# Public API  ##################################################################
def register_cli_skip_once_parser(cli_subparser):
    """
    register the ``skip-once`` subcommand parser.
    """
    skip_once_parser = cli_subparser.add_parser(
        "skip-once",
        aliases=["s"],
        help=_SKIP_ONCE_DOC,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    skip_once_parser.add_argument(
        "modules",
        metavar="MODULE",
        nargs="+",
        choices=SKIPPABLE_MODULES,
        help="module(s) to skip once on their next hook run",
    )
    # TODO add abbr

    add_verbose_arguments(skip_once_parser)

    skip_once_parser.set_defaults(func=_skip_once_main)
