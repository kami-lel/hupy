"""copy hook stub scripts"""

import argparse
import os
import pathlib
import shutil
import sys

from hupy.cli.cli_init import INIT_LOGGER_NAME, REPO_PATH_HELP, load_git_repo


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################


logger = getLogger(INIT_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

_HOOK_STUBS_DIR = pathlib.Path(__file__).resolve().parent.parent / "hook-stubs"

_PYTHON_PLACEHOLDER = "{{PYTHON}}"


_DESCRIPTION = __doc__ + """

copy default HUPy hook stub scripts into the repo's hooks directory (core.hooksPath if configured, otherwise .git/hooks/)
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


def _ich_main(args):
    """
    dispatch for the ``init-copy-hooks`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args, logger=logger)

    repo_path = args.repo_path
    force = args.force

    repo = load_git_repo(repo_path)

    repo_root = pathlib.Path(repo.working_tree_dir)
    hooks_dir = args.hooks_dir or _resolve_hooks_dir(repo)

    logger.enter("HUPy hook stub copy for: {}".format(repo_root))
    logger.debug("hooks dir: {}".format(hooks_dir))

    _copy_hook_stubs(hooks_dir, force)

    logger.done("HUPy hook stubs copied for: {}".format(repo_root))


# Public API  ##################################################################


def register_cli_ich_parser(cli_subparser):
    """
    register the ``init-copy-hooks`` subcommand parser.
    """
    ich_parser = cli_subparser.add_parser(
        "init-copy-hooks",
        help=__doc__,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ich_parser.add_argument(
        "repo_path",
        metavar="REPO_PATH",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=REPO_PATH_HELP,
    )

    ich_parser.add_argument(
        "--hooks-dir",
        dest="hooks_dir",
        metavar="HOOKS_DIR",
        type=pathlib.Path,
        default=None,
        help="override the folder the hook stub scripts are copied into",
    )

    ich_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="override an existing hook stub",
    )

    add_verbose_arguments(ich_parser)

    ich_parser.set_defaults(func=_ich_main)
