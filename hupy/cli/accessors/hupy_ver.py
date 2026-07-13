"""
hupy_ver.py

define the ``hupy-version`` accessor key's ``run_get`` and
``run_help``
"""

from importlib.metadata import version

# constants  ###################################################################
KEY = "hupy-version"
DOC = "get the installed HUPy version"


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the installed HUPy package version.
    """
    print(version("HUPy"))


def run_help(repo, state_file, logger, args):
    """
    print extended help for the ``hupy-version`` key.
    """
    print("""{}

read-only: reads the version HUPy was installed as, via
importlib.metadata; no value to set/unset.

usage:
  hupy get hupy-version""".format(DOC))
