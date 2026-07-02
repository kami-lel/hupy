"""
cli.py

main argument parser for the hupy command-line interface
"""

from argparse import ArgumentParser

from hupy.pch.parser import register_cli_pch_parser
from hupy.ttg.parser import register_cli_ttg_parser

__all__ = ("cli_parser", "cli_subparser")

# main parse  ##################################################################


def _cli_main(_):
    """
    dispatch when calling ``python -m hupy`` without subcommand.


    :param _: parsed arguments (unused)
    :type _: argparse.Namespace
    """
    cli_parser.print_help()


cli_parser = ArgumentParser(
    prog=__package__,
    description=__doc__,
)
cli_parser.set_defaults(func=_cli_main)
cli_subparser = cli_parser.add_subparsers(title="subcommands")

# register subcommands
register_cli_ttg_parser(cli_subparser)
register_cli_pch_parser(cli_subparser)
