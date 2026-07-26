import argparse
import os
import pathlib

from hupy import PROJ_LOGGER_NAME
from hupy.cli.cli_init import (
    REPO_PATH_HELP,
    load_git_repo,
)
from hupy.config_file.load_config import load_hupy_config
from hupy.state.state_file import HupyStateFile
from hupy.stub.update_stubs import check_hook_stubs, resolve_hooks_dir
from hupy.ver_grep.ver_grep import grep_version
from hupy.ver_grep.version_uniformity import check_version_uniformity


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_namespace,
    getLogger,
)

# logger  ######################################################################


logger = getLogger(PROJ_LOGGER_NAME + ".verify")
logger.propagate = False


# constants  ###################################################################

_VERIFY_DOC = "check that HUPy is correctly set up for a repository"

_DESCRIPTION = _VERIFY_DOC + """

read-only inspection; reports on:

- the config file (.hupy.config.jsonc) at repository root loads and
  validates against the schema
- the version string can be grepped per the VerGrep config
- every other configured version occurrence still carries that same
  version (Version Uniformity)
- the hook stubs installed in the repo's hooks directory match what
  is currently demanded

writes nothing and repairs nothing; run `hupy init` to fix what is
reported. exits nonzero only when the config file is missing or
malformed — hook stub drift is reported but does not affect the exit
code.
"""


# auxiliaries  #################################################################


def _report_hook_stub_drift(
    hooks_dir, missing_names, stale_names, unused_names
):
    """
    warn about every demanded-but-missing, drifted, and no-longer-
    demanded hook stub, pointing at ``hupy init`` as the repair
    """
    for hook_name in missing_names:
        logger.warning("missing hook stub: {}".format(hooks_dir / hook_name))

    for hook_name in stale_names:
        logger.warning(
            "hook stub differs from what HUPy renders: {}".format(
                hooks_dir / hook_name
            )
        )

    for hook_name in unused_names:
        logger.warning("prunable hook stub: {}".format(hooks_dir / hook_name))

    if missing_names or stale_names or unused_names:
        logger.note("run `hupy init` to bring the hooks dir back in shape")


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

    load_hupy_config(repo)
    logger.pass_("config file verified")

    state_file = HupyStateFile()

    version = grep_version(repo, state_file, "HEAD")
    logger.pass_("canonical version grepped: {!r}".format(version))

    check_version_uniformity(repo, state_file, "HEAD", is_report_only=True)

    hooks_dir = resolve_hooks_dir(repo)
    missing_names, stale_names, unused_names = check_hook_stubs(
        repo, hooks_dir=hooks_dir
    )

    if missing_names or stale_names or unused_names:
        _report_hook_stub_drift(
            hooks_dir, missing_names, stale_names, unused_names
        )
    else:
        logger.pass_("hook stubs verified")

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

    add_verbose_arguments(verify_parser)

    verify_parser.set_defaults(func=_verify_main)
