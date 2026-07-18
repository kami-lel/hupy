"""uninstall HUPy from the current repository"""

import argparse
import os
import pathlib

from hupy import PROJ_LOGGER_NAME
from hupy.cli.cli_init import load_git_repo, REPO_PATH_HELP
from hupy.config_file.write_config import remove_config_file
from hupy.stub.update_stubs import uninstall_hook_stubs

from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################

UNINSTALL_LOGGER_NAME = PROJ_LOGGER_NAME + ".uninstall"

logger = getLogger(UNINSTALL_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

_DESCRIPTION = __doc__ + """

performs:

- remove HUPy-managed hook stub scripts from the repo's hooks directory
  (core.hooksPath if configured, otherwise .git/hooks/;
  only files identified as HUPy-managed stubs are removed)
- remove the HUPy config file (.hupy.config.jsonc) from repository root

without --force, nothing is deleted: a dry run reports (via info logs)
what would be removed
"""


# auxiliaries  #################################################################


def _uninstall_main(args):
    """
    dispatch for the ``uninstall`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args)

    repo_path = args.repo_path
    repo = load_git_repo(repo_path)
    repo_root = pathlib.Path(repo.working_tree_dir)

    # no step flag given: run both steps (dft behavior)
    run_both = not (args.uninstall_hook_stubs or args.remove_config_file)

    logger.enter("HUPy Uninstallation for: {}".format(repo_root))

    if not args.force:
        logger.note("dry run: use --force to actually remove listed files")

    if run_both or args.uninstall_hook_stubs:
        uninstall_hook_stubs(repo, force=args.force)

    if run_both or args.remove_config_file:
        remove_config_file(repo, args.force)

    if args.force:
        logger.done("HUPy Uninstalled for: {}".format(repo_root))
    else:
        logger.done("dry run in: {}".format(repo_root))


# Public API  ##################################################################


def register_cli_uninstall_parser(cli_subparser):
    """
    register the ``uninstall`` subcommand parser.
    """
    uninstall_parser = cli_subparser.add_parser(
        "uninstall",
        help=__doc__,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    uninstall_parser.add_argument(
        "repo_path",
        metavar="REPO_PATH",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=REPO_PATH_HELP,
    )

    uninstall_parser.add_argument(
        "--uninstall-hook-stubs",
        dest="uninstall_hook_stubs",
        action="store_true",
        default=False,
        help="only remove the HUPy-managed hook stub scripts",
    )

    uninstall_parser.add_argument(
        "--remove-config-file",
        dest="remove_config_file",
        action="store_true",
        default=False,
        help="only remove the HUPy config file",
    )

    uninstall_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="actually remove the listed files instead of a dry run",
    )

    add_verbose_arguments(uninstall_parser)

    uninstall_parser.set_defaults(func=_uninstall_main)
