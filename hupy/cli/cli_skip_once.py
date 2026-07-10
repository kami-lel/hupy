"""flag HUPy modules to be skipped once on their next hook run"""

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

_MODULE_ABBR_TO_NAME = {
    "ver_grep": "ver-grep",
    "ttg": "triage-tag-gating",
    "pch": "prepend-commit-header",
    "bdc": "ban-direct-commit",
    "hb": "hook-bracket",
}

_MODULE_NAME_TO_ABBR = {
    name: abbr for abbr, name in _MODULE_ABBR_TO_NAME.items()
}

_SKIPPABLE_MODULE_CHOICES = tuple(_MODULE_ABBR_TO_NAME.keys()) + tuple(
    _MODULE_NAME_TO_ABBR.keys()
)

_SKIP_ONCE_DOC = "skip modules in next hook run"

_DESCRIPTION = __doc__ + """

modules: {}

each flagged module is skipped exactly once, consumed by the next
pre-commit/prepare-commit-msg run that checks it, regardless of its
is_disabled config setting
""".format(
    ", ".join(
        "{} ({})".format(name, abbr)
        for abbr, name in _MODULE_ABBR_TO_NAME.items()
    )
)


# helpers  #####################################################################


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
        for abbr in abbrs:
            if abbr not in state_file.skip_once:
                state_file.skip_once.append(abbr)

        logger.done("flagged for one-time skip: {}".format(", ".join(abbrs)))


# Public API  ##################################################################
def register_cli_skip_once_parser(cli_subparser):
    """
    register the ``skip-once`` subcommand parser.
    """
    skip_once_parser = cli_subparser.add_parser(
        "skip-once",
        aliases=["s"],
        help=_SKIP_ONCE_DOC,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    skip_once_parser.add_argument(
        "modules",
        metavar="MODULE",
        nargs="+",
        choices=_SKIPPABLE_MODULE_CHOICES,
        help="module(s) to skip once on their next hook run, by full "
        "name or abbr",
    )

    add_verbose_arguments(skip_once_parser)

    skip_once_parser.set_defaults(func=_skip_once_main)
