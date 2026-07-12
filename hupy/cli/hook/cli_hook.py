"""
cli_hook.py

define ``register_cli_hook_parser``, nesting git hook stage subcommands
"""

from hupy.cli.hook.cli_commit_msg import register_cli_commit_msg_parser
from hupy.cli.hook.cli_post_commit import register_cli_post_commit_parser
from hupy.cli.hook.cli_pre_commit import register_cli_pre_commit_parser
from hupy.cli.hook.cli_prepare_commit_msg import (
    register_cli_prepare_commit_msg_parser,
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

    register_cli_pre_commit_parser(hook_subparser)
    register_cli_prepare_commit_msg_parser(hook_subparser)
    register_cli_commit_msg_parser(hook_subparser)
    register_cli_post_commit_parser(hook_subparser)
