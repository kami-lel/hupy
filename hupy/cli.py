"""
cli.py

main argument parser for the hupy command-line interface
"""

from argparse import ArgumentParser

from hupy.pch.parser import register_cli_pch_parser
from hupy.setup.parser import register_cli_init_parser
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


# pre-commit stage  ############################################################


def _pre_commit_main(args):
    """
    dispatch when calling ``pre-commit`` without a subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    args.parser.print_help()


def _pre_commit_start_main(_):
    """
    dispatch for the ``pre-commit start`` subcommand.


    :param _: parsed arguments (unused)
    :type _: argparse.Namespace
    """
    pass  # Todo mpl pre-commit start


def _pre_commit_end_main(_):
    """
    dispatch for the ``pre-commit end`` subcommand.


    :param _: parsed arguments (unused)
    :type _: argparse.Namespace
    """
    pass  # Todo mpl pre-commit end


def _register_cli_pre_commit_parser(cli_subparser):
    """
    register the ``pre-commit`` subcommand group and its subcommands.
    """
    pre_commit_parser = cli_subparser.add_parser(
        "pre-commit",
        help="run utilities scoped to the pre-commit git hook stage",
    )
    pre_commit_parser.set_defaults(
        func=_pre_commit_main, parser=pre_commit_parser
    )
    pre_commit_subparser = pre_commit_parser.add_subparsers(title="subcommands")

    start_parser = pre_commit_subparser.add_parser(
        "start", help="mark the start of the pre-commit stage"
    )
    start_parser.set_defaults(func=_pre_commit_start_main)

    register_cli_ttg_parser(pre_commit_subparser)

    end_parser = pre_commit_subparser.add_parser(
        "end", help="mark the end of the pre-commit stage"
    )
    end_parser.set_defaults(func=_pre_commit_end_main)


# prepare-commit-msg stage  ####################################################


def _prepare_commit_msg_main(args):
    """
    dispatch when calling ``prepare-commit-msg`` without a subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    args.parser.print_help()


def _prepare_commit_msg_start_main(_):
    """
    dispatch for the ``prepare-commit-msg start`` subcommand.


    :param _: parsed arguments (unused)
    :type _: argparse.Namespace
    """
    pass  # Todo mpl prepare-commit-msg start


def _prepare_commit_msg_end_main(_):
    """
    dispatch for the ``prepare-commit-msg end`` subcommand.


    :param _: parsed arguments (unused)
    :type _: argparse.Namespace
    """
    pass  # Todo mpl prepare-commit-msg end


def _register_cli_prepare_commit_msg_parser(cli_subparser):
    """
    register the ``prepare-commit-msg`` subcommand group and its
    subcommands.
    """
    prepare_commit_msg_parser = cli_subparser.add_parser(
        "prepare-commit-msg",
        help="run utilities scoped to the prepare-commit-msg git hook stage",
    )
    prepare_commit_msg_parser.set_defaults(
        func=_prepare_commit_msg_main, parser=prepare_commit_msg_parser
    )
    prepare_commit_msg_subparser = prepare_commit_msg_parser.add_subparsers(
        title="subcommands"
    )

    start_parser = prepare_commit_msg_subparser.add_parser(
        "start", help="mark the start of the prepare-commit-msg stage"
    )
    start_parser.set_defaults(func=_prepare_commit_msg_start_main)

    register_cli_pch_parser(prepare_commit_msg_subparser)

    end_parser = prepare_commit_msg_subparser.add_parser(
        "end", help="mark the end of the prepare-commit-msg stage"
    )
    end_parser.set_defaults(func=_prepare_commit_msg_end_main)


cli_parser = ArgumentParser(
    prog=__package__,
    description=__doc__,
)
cli_parser.set_defaults(func=_cli_main)
cli_subparser = cli_parser.add_subparsers(title="subcommands")

# register subcommands
register_cli_init_parser(cli_subparser)
_register_cli_pre_commit_parser(cli_subparser)
_register_cli_prepare_commit_msg_parser(cli_subparser)


# Todo find version feature

# todo add configs and/or dry run feature
# todo use OpenAI to prepare commit message
# todo allow tmp skip some feature for next round
