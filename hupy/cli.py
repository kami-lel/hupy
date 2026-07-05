"""CLI of HUPy (Hooks Utility Python): git hook utilities for commit quality enforcement"""

from argparse import ArgumentParser

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.pch.cli_pch import register_cli_pch_parser
from hupy.setup.cli_init import register_cli_init_parser
from hupy.ttg.cli_ttg import register_cli_ttg_parser

__all__ = ("cli_parser", "cli_subparser")


# logger  ######################################################################


logger = kamilog.getLogger(PROJ_LOGGER_NAME)


# main parser  #################################################################


cli_parser = ArgumentParser(
    prog=__package__,
    description=__doc__,
)
cli_parser.set_defaults(func=lambda _: cli_parser.print_help())
cli_subparser = cli_parser.add_subparsers(title="subcommands")


# TODO move these parsers out

# pre-commit subparser  ########################################################


_PRE_COMMIT_DOC = "utilities for pre-commit git hook stage"


def _register_pre_commit_parser(subparser):
    pre_commit_parser = subparser.add_parser(
        "pre-commit",
        help=_PRE_COMMIT_DOC,
        description=_PRE_COMMIT_DOC,
    )
    pre_commit_parser.set_defaults(
        func=lambda _: pre_commit_parser.print_help(), parser=pre_commit_parser
    )

    pre_commit_subparser = pre_commit_parser.add_subparsers(title="subcommands")

    _register_pre_commit_start_parser(pre_commit_subparser)
    register_cli_ttg_parser(pre_commit_subparser)
    _register_pre_commit_end_parser(pre_commit_subparser)


# pre-commit start  ============================================================

_PRE_COMMIT_START_DOC = "mark start of pre-commit stage"


def _pre_commit_start_main(_):
    """
    dispatch for the ``pre-commit start`` subcommand.
    """
    logger.info("Perform HUPy hooks")
    logger.enter("Start of pre-commit stage")


def _register_pre_commit_start_parser(subparser):
    start_parser = subparser.add_parser(
        "start", help=_PRE_COMMIT_START_DOC, description=_PRE_COMMIT_START_DOC
    )
    start_parser.set_defaults(func=_pre_commit_start_main)


# pre-commit end  ==============================================================

_PRE_COMMIT_END_DOC = "mark end of pre-commit stage"


def _pre_commit_end_main(_):
    """
    dispatch for the ``pre-commit end`` subcommand.
    """
    logger.succ("End of pre-commit stage")


def _register_pre_commit_end_parser(subparser):
    end_parser = subparser.add_parser(
        "end", help=_PRE_COMMIT_END_DOC, description=_PRE_COMMIT_END_DOC
    )
    end_parser.set_defaults(func=_pre_commit_end_main)


# prepare-commit-msg subparser  ################################################

_PREPARE_COMMIT_MSG_DOC = "utilities for prepare-commit-msg git hook stage"


def _register_prepare_commit_msg_parser(subparser):
    prepare_commit_msg_parser = subparser.add_parser(
        "prepare-commit-msg",
        help=_PREPARE_COMMIT_MSG_DOC,
        description=_PREPARE_COMMIT_MSG_DOC,
    )
    prepare_commit_msg_parser.set_defaults(
        func=lambda _: prepare_commit_msg_parser.print_help(),
        parser=prepare_commit_msg_parser,
    )

    prepare_commit_msg_subparser = prepare_commit_msg_parser.add_subparsers(
        title="subcommands"
    )

    _register_prepare_commit_msg_start_parser(prepare_commit_msg_subparser)
    register_cli_pch_parser(prepare_commit_msg_subparser)
    _register_prepare_commit_msg_end_parser(prepare_commit_msg_subparser)


# prepare-commit-msg start  =====================================================

_PREPARE_COMMIT_MSG_START_DOC = "mark start of prepare-commit-msg stage"


def _prepare_commit_msg_start_main(_):
    """
    dispatch for the ``prepare-commit-msg start`` subcommand.
    """
    logger.enter("Start of prepare-commit-msg stage")


def _register_prepare_commit_msg_start_parser(subparser):
    start_parser = subparser.add_parser(
        "start",
        help=_PREPARE_COMMIT_MSG_START_DOC,
        description=_PREPARE_COMMIT_MSG_START_DOC,
    )
    start_parser.set_defaults(func=_prepare_commit_msg_start_main)


# prepare-commit-msg end  =======================================================

_PREPARE_COMMIT_MSG_END_DOC = "mark end of prepare-commit-msg stage"


def _prepare_commit_msg_end_main(_):
    """
    dispatch for the ``prepare-commit-msg end`` subcommand.
    """
    logger.succ("Start of prepare-commit-msg stage")
    logger.done("HUPy hooks Finished")


def _register_prepare_commit_msg_end_parser(subparser):
    end_parser = subparser.add_parser(
        "end",
        help=_PREPARE_COMMIT_MSG_END_DOC,
        description=_PREPARE_COMMIT_MSG_END_DOC,
    )
    end_parser.set_defaults(func=_prepare_commit_msg_end_main)


# register subparsers  #########################################################
register_cli_init_parser(cli_subparser)
_register_pre_commit_parser(cli_subparser)
_register_prepare_commit_msg_parser(cli_subparser)


# Todo find version feature

# todo add configs and/or dry run feature
# todo use OpenAI to prepare commit message
# todo allow tmp skip some feature for next round
