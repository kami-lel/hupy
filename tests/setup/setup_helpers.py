"""
setup_helpers.py

helpers for invoking the `init` CLI subcommand in isolation, and for
inspecting/seeding the resulting git config
"""

from argparse import ArgumentParser

import git

from hupy.setup.cli_init import register_cli_init_parser

# Public API  ##################################################################


def run_init_cli(args_list):
    """
    parse ``args_list`` against a standalone ``init`` subparser and
    dispatch it, mirroring how ``hupy.cli`` wires the real command.
    """
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    register_cli_init_parser(subparsers)
    args = parser.parse_args(["init"] + args_list)
    args.func(args)


def get_configured_hooks_path(repo_dir):
    """
    return the configured ``core.hooksPath`` for the repo at
    ``repo_dir``, or ``None`` if unset.
    """
    repo = git.Repo(str(repo_dir))
    with repo.config_reader() as reader:
        return reader.get_value("core", "hooksPath", default="") or None


def set_configured_hooks_path(repo_dir, value):
    """
    configure ``core.hooksPath`` to ``value`` for the repo at
    ``repo_dir``, simulating a pre-existing user configuration.
    """
    repo = git.Repo(str(repo_dir))
    with repo.config_writer() as writer:
        writer.set_value("core", "hooksPath", str(value))
