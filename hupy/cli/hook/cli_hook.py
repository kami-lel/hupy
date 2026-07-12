"""
cli_hook.py

define ``register_cli_hook_parser``, nesting git hook stage subcommands
"""

from hupy.cli.hook.cli_applypatch_msg import register_cli_applypatch_msg_parser
from hupy.cli.hook.cli_commit_msg import register_cli_commit_msg_parser
from hupy.cli.hook.cli_fsmonitor_watchman import (
    register_cli_fsmonitor_watchman_parser,
)
from hupy.cli.hook.cli_post_applypatch import (
    register_cli_post_applypatch_parser,
)
from hupy.cli.hook.cli_post_commit import register_cli_post_commit_parser
from hupy.cli.hook.cli_post_index_change import (
    register_cli_post_index_change_parser,
)
from hupy.cli.hook.cli_post_rewrite import register_cli_post_rewrite_parser
from hupy.cli.hook.cli_pre_applypatch import register_cli_pre_applypatch_parser
from hupy.cli.hook.cli_pre_auto_gc import register_cli_pre_auto_gc_parser
from hupy.cli.hook.cli_pre_commit import register_cli_pre_commit_parser
from hupy.cli.hook.cli_pre_merge_commit import (
    register_cli_pre_merge_commit_parser,
)
from hupy.cli.hook.cli_prepare_commit_msg import (
    register_cli_prepare_commit_msg_parser,
)
from hupy.cli.hook.cli_sendemail_validate import (
    register_cli_sendemail_validate_parser,
)

__all__ = ("register_cli_hook_parser",)

# constants  ###################################################################
_HOOK_DOC = "run git hook stage commands"


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

    # FIXME reorder
    register_cli_applypatch_msg_parser(hook_subparser)
    register_cli_pre_applypatch_parser(hook_subparser)
    register_cli_post_applypatch_parser(hook_subparser)
    register_cli_pre_commit_parser(hook_subparser)
    register_cli_pre_merge_commit_parser(hook_subparser)
    register_cli_prepare_commit_msg_parser(hook_subparser)
    register_cli_commit_msg_parser(hook_subparser)
    register_cli_post_commit_parser(hook_subparser)
    register_cli_post_rewrite_parser(hook_subparser)
    register_cli_pre_auto_gc_parser(hook_subparser)
    register_cli_post_index_change_parser(hook_subparser)
    register_cli_sendemail_validate_parser(hook_subparser)
    register_cli_fsmonitor_watchman_parser(hook_subparser)
