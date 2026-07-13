"""
hupy_ver.py

define the ``hupy-version`` accessor key's ``run_get`` and
``run_info``
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


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``hupy-version`` key.
    """
    print("""{}

usage:
  $ hupy get hupy-version""".format(DOC))
