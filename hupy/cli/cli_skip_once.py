"""
cli_skip_once.py

define the ``skip-once`` CLI subcommand, letting a HUPy module be
skipped for exactly one upcoming hook run
"""

import argparse
import os

import git

from hupy import PROJ_LOGGER_NAME
from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)
from hupy.state.open_state import open_state_file

# logger  ######################################################################

SKIP_ONCE_LOGGER_NAME = PROJ_LOGGER_NAME + ".skip_once"

logger = getLogger(SKIP_ONCE_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

SKIPPABLE_MODULE = ("vg", "ttg", "pch", "bdc", "hb")

_MODULE_ABBR_TO_NAME = dict(
    zip(
        SKIPPABLE_MODULE,
        # ordered to line up with SKIPPABLE_MODULE
        (
            "ver-grep",
            "triage-tag-gating",
            "prepend-commit-header",
            "ban-direct-commit",
            "hook-bracket",
        ),
    )
)

_MODULE_NAME_TO_ABBR = {
    name: abbr for abbr, name in _MODULE_ABBR_TO_NAME.items()
}


# auxiliary  ###################################################################
def _format_modules():
    return ",\n".join(
        "  {},\t{}".format(abbr, name)
        for abbr, name in _MODULE_ABBR_TO_NAME.items()
    )


_SKIP_ONCE_HELP = "skip module(s) in next hook run"

_SKIP_ONCE_DESCRIPTION = _SKIP_ONCE_HELP + """

MODULEs:
{}

each given module is skipped exactly once,
consumed by the next pre-commit/prepare-commit-msg""".format(_format_modules())


def _skip_once_main(args):
    """
    dispatch for the ``skip-once`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args, logger=logger)

    repo = git.Repo(os.getcwd(), search_parent_directories=True)

    abbrs = [
        _MODULE_NAME_TO_ABBR.get(module, module) for module in args.modules
    ]

    with open_state_file(repo) as state_file:
        if args.unset:
            state_file.skip_once.difference_update(abbrs)

            logger.done("unset one-time skip: {}".format(", ".join(abbrs)))
        else:
            state_file.skip_once.update(abbrs)

            logger.done("set one-time skip: {}".format(", ".join(abbrs)))


# Public API  ##################################################################
def register_cli_skip_once_parser(cli_subparser):
    """
    register the ``skip-once`` subcommand parser.
    """
    skip_once_parser = cli_subparser.add_parser(
        "skip-once",
        aliases=["s"],
        help=_SKIP_ONCE_HELP,
        description=_SKIP_ONCE_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    skip_once_parser.add_argument(
        "modules",
        metavar="MODULE",
        nargs="+",
        choices=tuple(_MODULE_ABBR_TO_NAME.keys())
        + tuple(_MODULE_NAME_TO_ABBR.keys()),
        help="module(s) to skip, v.s.",
    )

    skip_once_parser.add_argument(
        "-u",
        "--unset",
        action="store_true",
        help="unset one-time skip flag for module(s) instead",
    )

    add_verbose_arguments(skip_once_parser)

    skip_once_parser.set_defaults(func=_skip_once_main)
