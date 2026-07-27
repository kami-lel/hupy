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


def _run_uninstall_hook_stubs(args, repo):
    """
    step: remove HUPy-managed hook stub scripts from the repo's hooks dir
    """
    uninstall_hook_stubs(repo, force=args.force)


def _run_remove_config_file(args, repo):
    """
    step: remove the HUPy config file from the repo root
    """
    remove_config_file(repo, args.force)


# registry mapping each uninstall step's --only value to its runner
_UNINSTALL_STEPS = {
    "stubs": _run_uninstall_hook_stubs,
    "config": _run_remove_config_file,
}


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

    # no --only given: run every step (dft behavior)
    selected_steps = (
        [_UNINSTALL_STEPS[args.only]]
        if args.only
        else list(_UNINSTALL_STEPS.values())
    )

    logger.enter("HUPy Uninstallation for: {}".format(repo_root))

    if not args.force:
        logger.note("dry run: use --force to actually remove listed files")

    for run_step in selected_steps:
        run_step(args, repo)

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
        aliases=["u"],
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
        "--only",
        dest="only",
        choices=("stubs", "config"),
        default=None,
        help="remove only the hook stubs, or only the HUPy config "
        "file; default=both",
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
