"""create default config file"""

import argparse
import os
import pathlib

from hupy.cli.cli_init import INIT_LOGGER_NAME, REPO_PATH_HELP, load_git_repo
from hupy.config.write_config import write_default_config


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################


logger = getLogger(INIT_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################


_DESCRIPTION = __doc__ + """

create a default HUPy config file (.hupy.config.json) at repository root
"""


# helpers  #####################################################################


def _icc_main(args):
    """
    dispatch for the ``init-create-config`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args, logger=logger)

    repo_path = args.repo_path
    force = args.force

    repo = load_git_repo(repo_path)

    repo_root = pathlib.Path(repo.working_tree_dir)

    logger.enter("HUPy config creation for: {}".format(repo_root))

    write_default_config(repo_root, force)

    logger.done("HUPy config created for: {}".format(repo_root))


# Public API  ##################################################################


def register_cli_icc_parser(cli_subparser):
    """
    register the ``init-create-config`` subcommand parser.
    """
    icc_parser = cli_subparser.add_parser(
        "init-create-config",
        help=__doc__,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    icc_parser.add_argument(
        "repo_path",
        metavar="REPO_PATH",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=REPO_PATH_HELP,
    )

    icc_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="override an existing HUPy config file",
    )

    add_verbose_arguments(icc_parser)

    icc_parser.set_defaults(func=_icc_main)
