"""initialize HUPy in the current repository"""

import argparse
import os
import pathlib

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
    # TODO TODO mpl setups
    logger.done(
        "HUPy Initialized for: {} (hooks dir: {})".format(root_path, hooks_dir)
    )


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

    add_verbose_arguments(init_parser)

    init_parser.set_defaults(func=_init_main)
