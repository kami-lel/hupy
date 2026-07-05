"""CLI of HUPy (Hooks Utility Python): git hook utilities for commit quality enforcement"""

import os
from argparse import ArgumentParser

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.config.load_config import load_config
from hupy.pch.prepend_commit_header import prepend_commit_header
from hupy.setup.cli_init import register_cli_init_parser
from hupy.ttg.tt_gating import perform_triage_tags_gating

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


# pre-commit parser  ###########################################################


_PRE_COMMIT_DOC = "run pre-commit stage hooks"


def _pre_commit_main(args):
    """
    dispatch for the ``pre-commit`` subcommand: execute triage tag gating.
    """
    config = load_config(os.getcwd())
    kamilog.set_logging_level_by_namespace(
        args, verbosity=config.default_logger_verbosity
    )

    logger.enter("Start pre-commit stage")

    perform_triage_tags_gating(os.getcwd())

    logger.done("pre-commit HUPy hooks")


def _register_pre_commit_parser(subparser):
    pre_commit_parser = subparser.add_parser(
        "pre-commit",
        help=_PRE_COMMIT_DOC,
        description=_PRE_COMMIT_DOC,
    )
    kamilog.add_verbose_arguments(pre_commit_parser)
    pre_commit_parser.set_defaults(func=_pre_commit_main)


# prepare-commit-msg parser  ###################################################


_PREPARE_COMMIT_MSG_DOC = "run prepare-commit-msg stage hooks"


def _prepare_commit_msg_main(args):
    """
    dispatch for the ``prepare-commit-msg`` subcommand: execute prepend
    commit header.
    """
    config = load_config(os.getcwd())
    kamilog.set_logging_level_by_namespace(
        args, verbosity=config.default_logger_verbosity
    )

    logger.enter("Start prepare-commit-msg stage")

    prepend_commit_header(os.getcwd())

    logger.done("prepare-commit-msg HUPy hooks")


def _register_prepare_commit_msg_parser(subparser):
    prepare_commit_msg_parser = subparser.add_parser(
        "prepare-commit-msg",
        help=_PREPARE_COMMIT_MSG_DOC,
        description=_PREPARE_COMMIT_MSG_DOC,
    )
    kamilog.add_verbose_arguments(prepare_commit_msg_parser)
    prepare_commit_msg_parser.set_defaults(func=_prepare_commit_msg_main)


# register subparsers  #########################################################

register_cli_init_parser(cli_subparser)
_register_pre_commit_parser(cli_subparser)
_register_prepare_commit_msg_parser(cli_subparser)


# TODO find version feature

# todo add configs and/or dry run feature
# todo use OpenAI to prepare commit message
# todo allow tmp skip some feature for next round
