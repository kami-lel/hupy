"""
parser.py

init CLI parser and subcommand registration
"""


def _init_main(args):
    """
    dispatch for the ``init`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    pass  # TODO TODO mpl setups


def register_cli_init_parser(cli_subparser):
    """
    register the ``init`` subcommand parser.
    """
    init_parser = cli_subparser.add_parser(
        "init",
        help="initialize HUPy in the current repository",
    )
    init_parser.set_defaults(func=_init_main)
