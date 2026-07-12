import argparse
import os
import pathlib

from hupy import PROJ_LOGGER_NAME
from hupy.cli.cli_init import (
    HOOK_STUBS_DIR,
    REPO_PATH_HELP,
    _resolve_hooks_dir,
    load_git_repo,
)
from hupy.config_file.load_config import load_hupy_config
from hupy.state.open_state import open_state_file
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

- config file (.hupy.config.jsonc) at repository root loads and
  validates against the schema
- version string can be grepped per the VerGrep config
- every packaged hook stub is installed in the repo's hooks directory
"""


# auxiliaries  #################################################################


def _verify_hook_stubs(repo):
    """
    verify every HUPy hook stub is installed in ``repo``'s hooks dir
    (content of each installed file is not checked)


    :param repo: repository to verify
    :type repo: git.Repo
    :raises SystemExit: ``repo``'s hooks dir is missing one or more
            hook stub scripts
    :return: number of hook stub scripts verified
    :rtype: int
    """
    hooks_dir = _resolve_hooks_dir(repo)

    stub_names = {stub_file.name for stub_file in HOOK_STUBS_DIR.iterdir()}
    installed_names = (
        {installed_file.name for installed_file in hooks_dir.iterdir()}
        if hooks_dir.is_dir()
        else set()
    )

    missing_names = stub_names - installed_names
    if missing_names:
        for missing_name in sorted(missing_names):
            logger.fail("missing hook stub: {}".format(missing_name))
        raise SystemExit(1)

    return len(stub_names)


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

        cnt = _verify_hook_stubs(repo)
        logger.pass_("hook stubs exist, count: {}".format(cnt))

    logger.done("HUPy verification completed: {}".format(repo_root))


# TODO add / remove hook stub by demand


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

    add_verbose_arguments(verify_parser)

    verify_parser.set_defaults(func=_verify_main)
