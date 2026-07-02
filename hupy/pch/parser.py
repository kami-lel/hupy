"""
parser.py

prepend commit header CLI parser and subcommand registration
"""

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_verbosity,
)
from hupy.pch import prepend_commit_header


def _pch_main(args):
    """
    dispatch for the ``prepend_commit_header`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_verbosity(args, logger_name=PROJ_LOGGER_NAME)
    prepend_commit_header(os.getcwd())


def register_cli_pch_parser(cli_subparser):
    """
    register the ``prepend_commit_header`` subcommand parser.
    """
    pch_parser = cli_subparser.add_parser(
        "prepend_commit_header",
        aliases=["pch"],
        help="generate better commit message headers for merge commits",
    )
    add_verbose_arguments(pch_parser)
    pch_parser.set_defaults(func=_pch_main)
