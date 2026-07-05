"""
setup_helpers.py

helpers for invoking the `init` CLI subcommand in isolation, and for
inspecting the resulting git config
"""

# FiXME helpers (esp. read_hooks_path) target the superseded
# core.hooksPath design; rework once `init` writes .hupy.config.json +
# .git/hooks/ stubs instead, per CONTEXT.md's Hook Integration Model

from argparse import ArgumentParser

import git

from hupy.setup.parser import register_cli_init_parser

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


def read_hooks_path(repo_dir):
    """
    return the configured ``core.hooksPath`` for the repo at
    ``repo_dir``.
    """
    repo = git.Repo(str(repo_dir))
    with repo.config_reader() as reader:
        return reader.get_value("core", "hooksPath")
