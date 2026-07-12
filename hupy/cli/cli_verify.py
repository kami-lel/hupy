import argparse
import os
import pathlib

from hupy import PROJ_LOGGER_NAME
from hupy.cli.cli_init import (
    REPO_PATH_HELP,
    _resolve_hooks_dir,
    load_git_repo,
)
from hupy.config_file.load_config import load_hupy_config
from hupy.state.open_state import open_state_file
from hupy.stub.update_stubs import verify_hook_stubs
from hupy.ver_grep.ver_grep import grep_version


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################


logger = getLogger(PROJ_LOGGER_NAME + ".verify")
logger.propagate = False


# constants  ###################################################################

_VERIFY_DOC = "verify HUPy is setup for the repository"

_DESCRIPTION = _VERIFY_DOC + """

check that HUPy is correctly set up, verifying:

- config file (.hupy.config.jsonc) at repository root loads and validates against the schema
- version string can be grepped per the VerGrep config
- verify hook stubs installed in the repo's hooks directory match what's currently demanded
"""


# auxiliaries  #################################################################


def _verify_main(args):
    """
    dispatch for the ``verify`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_namespace(args)

    repo_path = args.repo_path

    repo = load_git_repo(repo_path)

    repo_root = pathlib.Path(repo.working_tree_dir)

    logger.enter("HUPy verify: {}".format(repo_root))

    with open_state_file(repo) as state_file:
        load_hupy_config(repo)
        logger.pass_("config file verified")
        version = grep_version(repo, state_file, "HEAD")
        logger.pass_("VerGrep verified, grepped: {!r}".format(version))

        verify_hook_stubs(
            _resolve_hooks_dir(repo),
            repo,
            force=args.force,
            update=args.update_hook_stubs,
        )
        logger.pass_("hook stubs verified/updated")

    logger.done("HUPy verification completed: {}".format(repo_root))


# Public API  ##################################################################
def register_cli_verify_parser(cli_subparser):
    """
    register the ``verify`` subcommand parser.
    """
    verify_parser = cli_subparser.add_parser(
        "verify",
        aliases=["v"],
        help=_VERIFY_DOC,
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    verify_parser.add_argument(
        "repo_path",
        metavar="REPO_PATH",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(os.getcwd()),
        help=REPO_PATH_HELP,
    )

    verify_parser.add_argument(
        "-u",
        "--update-hook-stubs",
        dest="update_hook_stubs",
        action="store_true",
        default=False,
        help=(
            "instead of just verify, perform hooks stub sync: "
            "add missing hook stubs and remove ones no longer demanded"
        ),
    )

    verify_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="with -u, also refresh already-installed hook stubs",
    )

    add_verbose_arguments(verify_parser)

    verify_parser.set_defaults(func=_verify_main)
