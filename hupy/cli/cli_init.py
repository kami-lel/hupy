"""set up HUPy in a repository, and bring an existing setup back into shape"""

import argparse
import os
import pathlib

import git

from hupy import PROJ_LOGGER_NAME
from hupy.config_file.write_config import sync_config_file
from hupy.stub.update_stubs import sync_hook_stubs

from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################

INIT_LOGGER_NAME = PROJ_LOGGER_NAME + ".init"

logger = getLogger(INIT_LOGGER_NAME)
logger.propagate = False


root_logger = getLogger(PROJ_LOGGER_NAME)
root_logger.propagate = False


# constants  ###################################################################

REPO_PATH_HELP = (
    "git repository path (or any of its subdirectories;) "
    "default=current working directory"
)

_DESCRIPTION = __doc__ + """

converges the repository onto what HUPy currently demands:

- installs the demanded hook stub scripts into the repo's hooks
  directory (core.hooksPath if configured, otherwise .git/hooks/;
  override with --hooks-dir)
- creates the HUPy config file (.hupy.config.jsonc) at repository
  root when it is absent

safe to run repeatedly: files already correct are left untouched,
missing files are written, and nothing is deleted or rewritten
unless you ask for it.
"""


# auxiliaries  #################################################################


def _run_sync_hook_stubs(args, repo):
    """
    step: converge the repo's hooks dir onto the demanded HUPy hook
    stub scripts
    """
    sync_hook_stubs(
        repo,
        hooks_dir=args.hooks_dir,
        force=args.force,
        prune=args.prune,
        dry_run=args.dry_run,
    )


def _run_sync_config_file(args, repo):
    """
    step: converge the repo's HUPy config file onto the default asset
    """
    sync_config_file(repo, force=args.force, dry_run=args.dry_run)


# registry mapping each init step's --only value to its runner
_INIT_STEPS = {
    "stubs": _run_sync_hook_stubs,
    "config": _run_sync_config_file,
}


def _init_main(args):
    """
    dispatch for the ``init`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args)

    repo_path = args.repo_path
    repo = load_git_repo(repo_path)
    repo_root = pathlib.Path(repo.working_tree_dir)

    # no --only given: run every step (dft behavior)
    selected_steps = (
        [_INIT_STEPS[args.only]] if args.only else list(_INIT_STEPS.values())
    )

    logger.enter("HUPy Initialization for: {}".format(repo_root))

    if args.dry_run:
        logger.note("dry run: reporting only, nothing is written or removed")

    for run_step in selected_steps:
        run_step(args, repo)

    logger.done("HUPy Initialized for: {}".format(repo_root))


# Public API  ##################################################################


def load_git_repo(repo_path):
    """
    load the Git repository containing ``repo_path``, searching
    parent directories if ``repo_path`` itself is not a repo root.


    :param repo_path: path to the repo root, or to any path inside it
    :type repo_path: str
    :raises SystemExit: ``repo_path`` is not inside a Git repository
    :return: the loaded repository
    :rtype: git.Repo
    """
    try:
        return git.Repo(repo_path, search_parent_directories=True)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError) as e:
        root_logger.exception("not a Git repository: {}".format(repo_path))
        raise SystemExit(1) from e


def register_cli_init_parser(cli_subparser):
    """
    register the ``init`` subcommand parser.
    """
    init_parser = cli_subparser.add_parser(
        "init",
        aliases=["i"],
        help=__doc__,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    init_parser.add_argument(
        "repo_path",
        metavar="REPO_PATH",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=REPO_PATH_HELP,
    )

    init_parser.add_argument(
        "--only",
        dest="only",
        choices=("stubs", "config"),
        default=None,
        help="converge only the hook stubs, or only the HUPy config "
        "file; default=both",
    )

    init_parser.add_argument(
        "--hooks-dir",
        dest="hooks_dir",
        metavar="HOOKS_DIR",
        type=pathlib.Path,
        default=None,
        help="override the folder the hook stub scripts are installed into",
    )

    init_parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        default=False,
        help="rewrite a hook stub or HUPy config file that already "
        "exists but differs from what HUPy demands",
    )

    init_parser.add_argument(
        "--prune",
        dest="prune",
        action="store_true",
        default=False,
        help="remove installed hook stubs that are no longer demanded",
    )

    init_parser.add_argument(
        "-n",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="report what would be written, removed, or rewritten, "
        "and change nothing",
    )

    add_verbose_arguments(init_parser)

    init_parser.set_defaults(func=_init_main)
