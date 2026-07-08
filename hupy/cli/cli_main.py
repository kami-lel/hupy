"""CLI of HUPy (Hooks Utility Python): git hook utilities for commit quality enforcement"""

from argparse import ArgumentParser

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import register_cli_init_parser
from hupy.cli.cli_pre_commit import register_cli_pre_commit_parser
from hupy.cli.cli_prepare_commit_msg import (
    register_cli_prepare_commit_msg_parser,
)

__all__ = ("cli_parser", "cli_subparser")


# logger  ######################################################################
logger = kamilog.getLogger(PROJ_LOGGER_NAME)


# main parser  #################################################################


cli_parser = ArgumentParser(
    prog="hupy",
    description=__doc__,
)
cli_parser.set_defaults(func=lambda _: cli_parser.print_help())
cli_subparser = cli_parser.add_subparsers(title="subcommands")


# register subparsers  #########################################################

register_cli_init_parser(cli_subparser)
register_cli_pre_commit_parser(cli_subparser)
register_cli_prepare_commit_msg_parser(cli_subparser)


# Todo add configs and/or dry run feature
# todo use OpenAI to prepare commit message
# Todo allow tmp skip some feature for next round
