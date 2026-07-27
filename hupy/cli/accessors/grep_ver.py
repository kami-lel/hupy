"""
grep_ver.py

define the ``grep-ver`` accessor key's ``run_get`` and ``run_info``
"""

from hupy.ver_grep.ver_grep import WORKTREE, grep_version

# constants  ###################################################################
KEY = "grep-ver"
DOC = "get current repository version string grepped"


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the version grepped from the worktree's version file, or an
    empty line if unconfigured, missing, or unmatched.
    """
    print(grep_version(repo, state_file, WORKTREE))


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``grep-ver`` key.
    """
    print("""{}

print the captured group from the first entry in
vg.version_occurrences (the canonical version source);

empty when VerGrep is unconfigured, disabled, skipped,
or the pattern doesn't match

usage:
  $ hupy get grep-ver""".format(DOC))
