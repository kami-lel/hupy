"""initialize HUPy in the current repository"""

import argparse
import os
import pathlib
import shutil
import sys

import git

from hupy import PROJ_LOGGER_NAME
from hupy.config_file.write_config import create_default_config_file

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

_HOOK_STUBS_DIR = (
    pathlib.Path(__file__).resolve().parent.parent / "assets" / "hook-stubs"
)

_PYTHON_PLACEHOLDER = "{{PYTHON}}"


_DESCRIPTION = __doc__ + """

performs:

- copy default HUPy hook stub scripts into the repo's hooks directory
  (core.hooksPath if configured, otherwise .git/hooks/;
  override with --hooks-dir)
- create a default HUPy config file (.hupy.config.json) at repository root
"""


# helpers  #####################################################################


def _resolve_hooks_dir(repo):
    """
    resolve ``repo``'s actual git hooks directory, honoring
    ``core.hooksPath`` if configured.
    """
    with repo.config_reader() as reader:
        configured = reader.get_value("core", "hooksPath", default="")

    if configured:
        return pathlib.Path(repo.working_tree_dir) / configured

    return pathlib.Path(repo.git_dir) / "hooks"


def _copy_hook_stubs(hooks_dir, force):
    """
    copy the default HUPy hook stub scripts into ``hooks_dir``
    """
    logger.enter("copy hook stubs")
    hooks_dir.mkdir(parents=True, exist_ok=True)

    for stub_file in _HOOK_STUBS_DIR.iterdir():
        target_path = hooks_dir / stub_file.name

        if target_path.exists():
            if not force:
                logger.error(
                    "hook already exists (use --force to override): {}".format(
                        target_path
                    )
                )
                raise SystemExit(1)

            logger.warning("overwrite existing hook: {}".format(target_path))

        content = stub_file.read_text(encoding="utf-8")
        content = content.replace(_PYTHON_PLACEHOLDER, sys.executable)
        target_path.write_text(content, encoding="utf-8")
        shutil.copymode(stub_file, target_path)

        logger.debug("hook stub installed: {}".format(target_path))


def _run_copy_hooks(args, repo):
    """
    step: copy default HUPy hook stub scripts into the repo's hooks dir.
    """
    hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)
    logger.debug("hooks dir: {}".format(hooks_dir))
    _copy_hook_stubs(hooks_dir, args.force)


def _run_create_config_file(args, repo):
    """
    step: create a default HUPy config file at repository root.
    """
    create_default_config_file(repo, args.force)


# registry mapping each init step to its arg dest and runner;  add a new
# step by appending a (dest, runner) pair here
_INIT_STEPS = [
    ("copy_hooks", _run_copy_hooks),
    ("create_config_file", _run_create_config_file),
]


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

    selected_steps = [
        (dest, run_step)
        for dest, run_step in _INIT_STEPS
        if getattr(args, dest)
    ]
    # no step flag given: run every step (dft behavior)
    if not selected_steps:
        selected_steps = _INIT_STEPS

    logger.enter("HUPy Initialization for: {}".format(repo_root))

    for dest, run_step in selected_steps:
        logger.debug("running init step: {}".format(dest))
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
        "--copy-hooks",
        dest="copy_hooks",
        action="store_true",
        default=False,
        help="only copy the hook stub scripts",
    )

    init_parser.add_argument(
        "--create-config-file",
        dest="create_config_file",
        action="store_true",
        default=False,
        help="only create the HUPy config file",
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
