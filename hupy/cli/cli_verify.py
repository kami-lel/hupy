"""verify the HUPy config file"""

import argparse
import os
import pathlib

from hupy import PROJ_LOGGER_NAME
from hupy.cli.cli_init import REPO_PATH_HELP, load_git_repo
from hupy.config_file.load_config import load_hupy_config
from hupy.state.open_state import open_state_file
from hupy.ver_grep.ver_grep import grep_version


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################


logger = getLogger(PROJ_LOGGER_NAME + ".verify")
logger.propagate = False


# constants  ###################################################################


_DESCRIPTION = __doc__ + """

validate the HUPy config file (.hupy.config.jsonc) at repository root
"""


# helpers  #####################################################################


def _verify_main(args):
    """
    dispatch for the ``verify`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args)

    repo_path = args.repo_path

    repo = load_git_repo(repo_path)

    repo_root = pathlib.Path(repo.working_tree_dir)

    logger.enter("HUPy verify: {}".format(repo_root))

    with open_state_file(repo) as state_file:
        load_hupy_config(repo)
        logger.pass_("config file verified")
        version = grep_version(repo, state_file, "HEAD")
        logger.pass_("VerGrep verified, grepped: {!r}".format(version))

        # TODO add assert stubs existed w/ counting
        logger.pass_("hook stubs exist")

    logger.done("HUPy verification completed: {}".format(repo_root))


# Public API  ##################################################################


def register_cli_verify_parser(cli_subparser):
    """
    register the ``verify`` subcommand parser.
    """
    verify_parser = cli_subparser.add_parser(
        "verify",
        aliases=["v"],
        help=__doc__,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    verify_parser.add_argument(
        "repo_path",
        metavar="REPO_PATH",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=REPO_PATH_HELP,
    )

    add_verbose_arguments(verify_parser)

    verify_parser.set_defaults(func=_verify_main)
