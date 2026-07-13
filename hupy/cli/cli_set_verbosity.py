"""
cli_set_verbosity.py

define the ``set-verbosity`` CLI subcommand, setting the base logging
verbosity used during hook runs
"""

# FIXME use accessor

import os

from hupy import PROJ_LOGGER_NAME
from hupy.cli.cli_init import load_git_repo
from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)
from hupy.state.open_state import open_state_file

# logger  ######################################################################

root_logger = getLogger(PROJ_LOGGER_NAME)
root_logger.propagate = False


# constants  ###################################################################

_DEFAULT_VERBOSITY = 1

_SET_VERBOSITY_HELP = "set verbosity number for logger during hooks"


def _set_verbosity_main(args):
    """
    dispatch for the ``set-verbosity`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args, logger=root_logger)

    repo = load_git_repo(os.getcwd())

    with open_state_file(repo) as state_file:
        state_file.hooks_logger_verbosity = args.verbosity

        root_logger.done("logger verbosity set: {}".format(args.verbosity))


# Public API  ##################################################################
def register_cli_set_verbosity_parser(cli_subparser):
    """
    register the ``set-verbosity`` subcommand parser.
    """
    set_verbosity_parser = cli_subparser.add_parser(
        "set-verbosity",
        aliases=["sv"],
        help=_SET_VERBOSITY_HELP,
        description=_SET_VERBOSITY_HELP,
    )

    set_verbosity_parser.add_argument(
        "verbosity",
        metavar="VERBOSITY",
        nargs="?",
        type=int,
        default=_DEFAULT_VERBOSITY,
        help="verbosity number to set; default={}".format(_DEFAULT_VERBOSITY),
    )

    add_verbose_arguments(set_verbosity_parser)

    set_verbosity_parser.set_defaults(func=_set_verbosity_main)
