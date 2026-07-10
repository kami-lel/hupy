"""initialize HUPy in the current repository"""

import argparse
import os
import pathlib

import git

from hupy import PROJ_LOGGER_NAME
from hupy.config.write_config import create_default_config_file


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

performs:

- copy default HUPy hook stub scripts into the repo's hooks directory
  (core.hooksPath if configured, otherwise .git/hooks/;
  override with --hooks-dir)
- create a default HUPy config file (.hupy.config.json) at repository root
"""


# helpers  #####################################################################


def _init_main(args):
    """
    dispatch for the ``init`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    # deferred import: cli_ich imports from this module at load time,
    # so importing it back at module level here would create a cycle
    from hupy.cli.cli_ich import _copy_hook_stubs, _resolve_hooks_dir

    set_logging_level_by_namespace(args, logger=logger)

    repo_path = args.repo_path
    force = args.force

    repo = load_git_repo(repo_path)

    repo_root = pathlib.Path(repo.working_tree_dir)
    hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)

    logger.enter("HUPy Initialization for: {}".format(repo_root))
    logger.debug("hooks dir: {}".format(hooks_dir))

    _copy_hook_stubs(hooks_dir, force)
    create_default_config_file(repo, force)

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
        "--hooks-dir",
        dest="hooks_dir",
        metavar="HOOKS_DIR",
        type=pathlib.Path,
        default=None,
        help="override the folder the hook stub scripts are copied into",
    )

    init_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="override an existing hook stub and/or HUPy config file",
    )

    add_verbose_arguments(init_parser)

    init_parser.set_defaults(func=_init_main)
