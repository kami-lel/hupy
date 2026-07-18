"""
grep_ver.py

define the ``grep-ver`` accessor key's ``run_get`` and ``run_info``
"""

from hupy.ver_grep.ver_grep import grep_version

# constants  ###################################################################
KEY = "grep-ver"
DOC = "get current repository version string grepped"


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the version grepped from HEAD's version file, or an empty
    line if unconfigured, missing, or unmatched.
    """
    print(grep_version(repo, state_file, "HEAD"))


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``grep-ver`` key.
    """
    print("""{}

print the captured group from vg.version_line_pattern
matched against vg.version_file;

empty when VerGrep is unconfigured, disabled, skipped,
or the pattern doesn't match

usage:
  $ hupy get grep-ver""".format(DOC))
