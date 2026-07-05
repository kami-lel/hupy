"""initialize HUPy in the current repository"""

# Fixme whole module implements the superseded scripts/hupy-hooks/ +
# core.hooksPath design; rework to write .hupy.config.json + .git/hooks/
# stubs per the current Hook Integration Model in CONTEXT.md

import argparse
import os
import pathlib
import shutil

import git

from hupy.setup import SETUP_LOGGER_NAME


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_verbosity,
    getLogger,
)

# logger  ######################################################################

logger = getLogger(SETUP_LOGGER_NAME)


# constants  ###################################################################


_DESCRIPTION = __doc__ + """

performs:

- copies the default HUPy hooks scripts into REPO_ROOT/scripts/hupy-hooks/,
  (or into --hooks-dir)
- configures git to run hooks from above path,
  instead of default untracked .git/hooks/
"""

_HOOKS_TEMPLATES_DIR = (
    pathlib.Path(__file__).resolve().parent.parent / "default-hupy-hooks"
)

# helpers  #####################################################################


def _copy_hooks_scripts(hooks_dir, force):
    # Fixme superseded — replace with writing a default .hupy.config.json
    # plus copying thin stubs straight into .git/hooks/, no hooks_dir
    """
    copy the default HUPy hooks scripts into ``hooks_dir``
    """
    logger.enter("copy hooks scripts")
    if hooks_dir.exists():
        if not force:
            logger.error(
                "hooks dir already exists (use --force to override): {}".format(
                    hooks_dir
                )
            )
            raise SystemExit(1)

        logger.warning(
            "override existing hooks scripts in: {}".format(hooks_dir)
        )
    else:
        hooks_dir.mkdir(parents=True)

    for template_file in _HOOKS_TEMPLATES_DIR.iterdir():
        target_path = hooks_dir / template_file.name
        logger.debug("hook script copied: {}".format(target_path))
        shutil.copy2(template_file, target_path)


def _configure_repo_hooks_path(repo, hooks_dir):
    # Fixme superseded — core.hooksPath is no longer set under the new
    # design; hooks go directly into the default .git/hooks/ location
    """
    configure git's ``core.hooksPath`` for ``repo``
    """
    logger.enter("configure git hooks path")

    try:
        with repo.config_writer() as writer:
            writer.set_value("core", "hooksPath", str(hooks_dir))
    except Exception as e:
        logger.exception(
            "failed to set core.hooksPath to: {}".format(hooks_dir)
        )
        raise SystemExit(1) from e


def _init_main(args):
    """
    dispatch for the ``init`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_verbosity(args, logger=logger)

    root_path = args.repo_root
    force = args.force

    try:
        repo = git.Repo(root_path, search_parent_directories=True)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError) as e:
        logger.exception("not a Git repository: {}".format(root_path))
        raise SystemExit(1) from e

    repo_root = pathlib.Path(repo.working_tree_dir)
    # Fixme hooks_dir/scripts-hupy-hooks resolution is superseded; new
    # design writes .git/hooks/ stubs directly, no hooks_dir needed
    hooks_dir = args.hooks_dir or (repo_root / "scripts" / "hupy-hooks")

    logger.enter("HUPy Initialization for: {}".format(repo_root))
    logger.debug("hook scripts dir: {}".format(hooks_dir))

    _copy_hooks_scripts(hooks_dir, force)
    _configure_repo_hooks_path(repo, hooks_dir)

    logger.done("HUPy Initialized for: {}".format(repo_root))


# Public API  ##################################################################
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
        "repo_root",
        metavar="REPO_ROOT",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=(
            "path to the git repository (or any of its subdirectories;) "
            "default=current working directory"
        ),
    )

    # Fixme --hooks-dir is superseded — no longer applicable once hooks
    # move to the fixed .git/hooks/ location
    init_parser.add_argument(
        "--hooks-dir",
        dest="hooks_dir",
        metavar="HOOKS_DIR",
        type=pathlib.Path,
        default=None,
        help="specify alternative folder to place all HUPy hooks scripts",
    )

    init_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="override existing hooks scripts",
    )

    add_verbose_arguments(init_parser)

    init_parser.set_defaults(func=_init_main)
