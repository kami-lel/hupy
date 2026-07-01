"""main parser for the hupy command-line interface"""

import os
from argparse import ArgumentParser

from .kamilog import add_verbose_arguments, set_logging_level_by_verbosity
from .tt_gating import logger as tt_gating_logger, perform_triage_tags_gating

__all__ = ("cli_parser", "cli_subparser")


# main parse  ##################################################################


def _cli_main(_):
    # when calling ``python -m hupy``
    cli_parser.print_help()


cli_parser = ArgumentParser(
    prog=__package__,
    description=__doc__,
)
cli_parser.set_defaults(func=_cli_main)
cli_subparser = cli_parser.add_subparsers(title="subcommands")


# ttg parse  ###################################################################


def _tt_gating_main(args):
    # dispatch for the ``triage_tag_gating`` subcommand
    set_logging_level_by_verbosity(args, logger=tt_gating_logger)
    perform_triage_tags_gating(os.getcwd())


# register ``triage_tag_gating`` subcommand parser
tt_gating_parser = cli_subparser.add_parser(
    "triage_tag_gating",
    aliases=["ttg"],
    help="gate commits by triage tag presence on protected branches",
)
add_verbose_arguments(tt_gating_parser)
tt_gating_parser.set_defaults(func=_tt_gating_main)
