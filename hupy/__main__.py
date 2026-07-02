"""
__main__.py

entry point for ``python -m hupy``
"""

from hupy.cli import cli_parser


def main():
    """
    parse arguments and dispatch to the requested subcommand.
    """
    args = cli_parser.parse_args()
    args.func(args)  # call respective main function


if __name__ == "__main__":
    main()
