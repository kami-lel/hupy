"""
cli_hook.py

define the generic git hook stage runner and
``register_cli_hook_parser``, nesting each stage's subcommand beneath
``hook``
"""

import os


from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.cli_init import load_git_repo
from hupy.cli.hooks import (
    applypatch_msg,
    commit_msg,
    fsmonitor_watchman,
    post_applypatch,
    post_checkout,
    post_commit,
    post_index_change,
    post_merge,
    post_rewrite,
    pre_applypatch,
    pre_auto_gc,
    pre_commit,
    pre_merge_commit,
    pre_push,
    pre_rebase,
    prepare_commit_msg,
    sendemail_validate,
)
from hupy.hb.perform_hook_brackets import perform_hook_brackets
from hupy.state.open_state import open_state_file

__all__ = ("register_cli_hook_parser",)


# logger  ######################################################################
proj_logger = kamilog.getLogger(PROJ_LOGGER_NAME)

# constants  ###################################################################
_HOOK_DOC = "run git hook stage commands"

HOOK_STAGE_START = "Start"
HOOK_STAGE_NOOP = "No Operation in this HUPy version, except HB"
HOOK_STAGE_FINISHED = "Finished"


# generic stage runner  ########################################################
def _run_hook_stage(hook_name, args, *, features=None, after=None, on_done=None):
    """
    dispatch shared by every git hook stage subcommand: open
    repo/state, run the ``hb`` lead bracket, the stage's own
    ``features`` (or a noop log when it has none), the ``hb`` trail
    bracket, ``after``, the succ log, then ``on_done``.
    """
    repo = load_git_repo(os.getcwd())
    logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + hook_name)
    logger.propagate = False

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )
        logger.enter(HOOK_STAGE_START)

        perform_hook_brackets(repo, state_file, hook_name, True, args.hook_args)

        if features is not None:
            features(repo, state_file, proj_logger, logger)
        else:
            logger.debug(HOOK_STAGE_NOOP)

        perform_hook_brackets(
            repo, state_file, hook_name, False, args.hook_args
        )

        if after is not None:
            after(repo, state_file, proj_logger, logger)

        logger.succ(HOOK_STAGE_FINISHED)

        if on_done is not None:
            on_done(repo, state_file, proj_logger, logger)


def _register_hook_stage(hook_subparser, mod):
    """
    register one stage module's subparser, routed through
    ``_run_hook_stage`` with that module's ``run_features``/
    ``run_after``/``run_done`` (each optional).
    """
    doc = "run {} stage hooks".format(mod.HOOK_NAME)
    stage_parser = hook_subparser.add_parser(
        mod.HOOK_NAME, help=doc, description=doc
    )
    stage_parser.add_argument(
        "hook_args",
        nargs="*",
        help="raw arguments forwarded",
    )
    kamilog.add_verbose_arguments(stage_parser)
    stage_parser.set_defaults(
        func=lambda args, mod=mod: _run_hook_stage(
            mod.HOOK_NAME,
            args,
            features=getattr(mod, "run_features", None),
            after=getattr(mod, "run_after", None),
            on_done=getattr(mod, "run_done", None),
        )
    )


# Public API  ##################################################################
def register_cli_hook_parser(cli_subparser):
    """
    register the ``hook`` subcommand parser, nesting the individual
    git hook stage runners beneath it.
    """
    hook_parser = cli_subparser.add_parser(
        "hook",
        help=_HOOK_DOC,
        description=_HOOK_DOC,
    )
    hook_parser.set_defaults(func=lambda _: hook_parser.print_help())
    hook_subparser = hook_parser.add_subparsers(title="hook stages")

    _register_hook_stage(hook_subparser, pre_commit)
    _register_hook_stage(hook_subparser, prepare_commit_msg)
    _register_hook_stage(hook_subparser, commit_msg)
    _register_hook_stage(hook_subparser, post_commit)

    _register_hook_stage(hook_subparser, pre_merge_commit)
    _register_hook_stage(hook_subparser, post_merge)

    _register_hook_stage(hook_subparser, pre_rebase)
    _register_hook_stage(hook_subparser, post_rewrite)

    _register_hook_stage(hook_subparser, applypatch_msg)
    _register_hook_stage(hook_subparser, pre_applypatch)
    _register_hook_stage(hook_subparser, post_applypatch)

    _register_hook_stage(hook_subparser, pre_auto_gc)
    _register_hook_stage(hook_subparser, post_index_change)
    _register_hook_stage(hook_subparser, sendemail_validate)
    _register_hook_stage(hook_subparser, fsmonitor_watchman)
    _register_hook_stage(hook_subparser, post_checkout)
    _register_hook_stage(hook_subparser, pre_push)
