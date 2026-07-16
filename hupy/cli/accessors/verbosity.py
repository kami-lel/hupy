"""
verbosity.py

define the ``verbosity`` accessor key's ``run_get``, ``run_set``,
and ``run_info``
"""

from hupy.state.state_file import HupyStateFile

# Fixme consider upd kamilog w/ exposed verbosity


# constants  ###################################################################
KEY = "verbosity"
DOC = "logger's verbosity used during hook runs"

_DEFAULT_VERBOSITY = HupyStateFile.model_fields[
    "hooks_logger_verbosity"
].default


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the current base logging verbosity.
    """
    print(state_file.hooks_logger_verbosity)


def run_set(repo, state_file, logger, args):
    """
    set the base logging verbosity; no VALUE resets to the default;
    -v/-q offset the resulting value.
    """
    base = int(args.value[0]) if args.value else _DEFAULT_VERBOSITY
    verbosity = base + args.verbose - args.quiet

    state_file.hooks_logger_verbosity = verbosity

    logger.done("verbosity set: {}".format(verbosity))


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``verbosity`` key.
    """
    print("""{}

value: integer, higher = more verbose
  >=3   debug
   2    enter
   1    info (default)
   0    done
  -1    warning
  -2    error
  <=-3  critical

usage:
  $ hupy set verbosity VALUE
  $ hupy set verbosity VALUE -v/-q
  $ hupy set verbosity -v/-q
  $ hupy get verbosity""".format(DOC))
