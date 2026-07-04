"""initialize HUPy in the current repository"""

import argparse
import os
import pathlib
import shutil

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


def _init_main(args):
    """
    dispatch for the ``init`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_verbosity(args, logger=logger)

    logger.enter("HUPy Initialization")
    root_path = args.repo_root
    hooks_dir = args.hooks_dir or root_path / "scripts" / "hupy-hooks"
    force = args.force

    # copy hooks scripts  ------------------------------------------------------
    if hooks_dir.exists():
        if not force:
            logger.critical(
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

    # set up git hooksPath  ----------------------------------------------------
    # TODO set up git hooksPath

    logger.done("HUPy Initialized for: {}".format(root_path))


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
            "path to the git repository to initialize; "
            "default=current working directory"
        ),
    )

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
