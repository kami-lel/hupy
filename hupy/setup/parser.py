"""initialize HUPy in the current repository"""

from hupy.setup import SETUP_LOGGER_NAME


from hupy.kamilog import (
    add_verbose_arguments,
    set_logging_level_by_verbosity,
    getLogger,
)

# logger  ######################################################################

logger = getLogger(SETUP_LOGGER_NAME)

# helpers  #####################################################################


def _init_main(args):
    """
    dispatch for the ``init`` subcommand.


    :param args: parsed arguments from argparse
    :type args: argparse.Namespace
    """
    set_logging_level_by_verbosity(SETUP_LOGGER_NAME)
    # TODO TODO mpl setups


# Public API  ##################################################################
def register_cli_init_parser(cli_subparser):
    """
    register the ``init`` subcommand parser.
    """
    init_parser = cli_subparser.add_parser(
        "init",
        help=__doc__,
        description=__doc__,
    )

    add_verbose_arguments(init_parser)

    init_parser.set_defaults(func=_init_main)
