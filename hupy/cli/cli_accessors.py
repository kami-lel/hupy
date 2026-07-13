"""
cli_accessors.py

define the generic state-key accessor runner and
``register_cli_accessors_parser``, nesting each registered key's
subcommand beneath ``get``/``set``/``unset``
"""

import os

from hupy import PROJ_LOGGER_NAME, kamilog
from hupy.cli.accessors import hupy_ver
from hupy.cli.cli_init import load_git_repo
from hupy.state.open_state import open_state_file

__all__ = ("register_cli_accessors_parser",)

# constants  ###################################################################
_ACCESSORS = (hupy_ver,)

_GET_DOC = "get a HUPy state key's current value"
_SET_DOC = "set a HUPy state key's value"
_UNSET_DOC = "unset a HUPy state key's value"


# generic key runner  ##########################################################
def _run_accessor(op_name, mod, args):
    """
    dispatch shared by every accessor key subcommand: open
    repo/state, build the key's logger, run the key module's
    ``run_{op_name}(repo, state_file, logger, args)``.
    """
    repo = load_git_repo(os.getcwd())
    logger = kamilog.getLogger(PROJ_LOGGER_NAME + "." + mod.KEY)
    logger.propagate = False

    with open_state_file(repo) as state_file:
        kamilog.set_logging_level_by_namespace(
            args, verbosity=state_file.hooks_logger_verbosity
        )

        run = getattr(mod, "run_" + op_name)
        run(repo, state_file, logger, args)


def _dispatch_accessor(op_name, mod, args, key_parser):
    """
    resolve a key subcommand invocation: ``-h`` routes to the key
    module's ``run_help`` (falling back to the ordinary argparse help
    when the module has none), else falls through to
    ``_run_accessor``.
    """
    if args.help:
        if getattr(mod, "run_help", None) is not None:
            _run_accessor("help", mod, args)
        else:
            key_parser.print_help()
        return

    _run_accessor(op_name, mod, args)


def _register_accessor_op(op_subparser, op_name, mod, *, needs_value):
    """
    register one key module's subparser under the ``op_name``
    (``get``/``set``/``unset``) command, only when the module defines
    ``run_{op_name}``.
    """
    run = getattr(mod, "run_" + op_name, None)
    if run is None:
        return

    key_parser = op_subparser.add_parser(
        mod.KEY, help=mod.DOC, description=mod.DOC, add_help=False
    )
    key_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="show this help message and exit",
    )
    if needs_value:
        key_parser.add_argument(
            "value",
            metavar="VALUE",
            nargs="*",
            help="value(s) to {}".format(op_name),
        )
    kamilog.add_verbose_arguments(key_parser)
    key_parser.set_defaults(
        func=lambda args, mod=mod, op_name=op_name, key_parser=key_parser: (
            _dispatch_accessor(op_name, mod, args, key_parser)
        )
    )


# Public API  ##################################################################
def register_cli_accessors_parser(cli_subparser):
    """
    register the ``get``/``set``/``unset`` subcommand parsers, nesting
    each registered key's subcommand beneath them.
    """
    get_parser = cli_subparser.add_parser(
        "get", help=_GET_DOC, description=_GET_DOC
    )
    get_parser.set_defaults(func=lambda _: get_parser.print_help())
    get_subparser = get_parser.add_subparsers(title="keys")

    set_parser = cli_subparser.add_parser(
        "set", help=_SET_DOC, description=_SET_DOC
    )
    set_parser.set_defaults(func=lambda _: set_parser.print_help())
    set_subparser = set_parser.add_subparsers(title="keys")

    unset_parser = cli_subparser.add_parser(
        "unset", help=_UNSET_DOC, description=_UNSET_DOC
    )
    unset_parser.set_defaults(func=lambda _: unset_parser.print_help())
    unset_subparser = unset_parser.add_subparsers(title="keys")

    for mod in _ACCESSORS:
        _register_accessor_op(get_subparser, "get", mod, needs_value=False)
        _register_accessor_op(set_subparser, "set", mod, needs_value=True)
        _register_accessor_op(unset_subparser, "unset", mod, needs_value=True)
