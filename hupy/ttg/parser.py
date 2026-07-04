"""
parser.py

triage-tag-gating CLI parser and subcommand registration
"""

import os

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_verbosity,
)
from hupy.ttg.tt_gating import perform_triage_tags_gating


def _tt_gating_main(args):
    """
    dispatch for the ``triage-tag-gating`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_verbosity(args, logger_name=PROJ_LOGGER_NAME)
    perform_triage_tags_gating(os.getcwd())


def register_cli_ttg_parser(cli_subparser):
    """
    register the ``triage-tag-gating`` subcommand parser onto the
    given (``pre-commit`` stage) subparser.
    """
    tt_gating_parser = cli_subparser.add_parser(
        "triage-tag-gating",
        help="gate commits by triage tag presence on protected branches",
    )
    add_verbose_arguments(tt_gating_parser)
    tt_gating_parser.set_defaults(func=_tt_gating_main)
