"""
commit_type.py

define the ``current-commit-type`` accessor key's ``run_get`` and
``run_info``
"""

from hupy.cbm.get_current_commit_type import get_current_commit_type

# constants  ###################################################################
KEY = "current-commit-type"
DOC = "get the current in-progress commit's type"


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the current in-progress commit's :class:`CommitType`.
    """
    print(get_current_commit_type(repo))


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``current-commit-type`` key.
    """
    print("""{}

value is one of:
REGULAR_COMMIT, OTHER_COMMIT, FEATURE_LANDING, VERSION_RELEASE,
SYNC_BACKPORT, CATCH_UP, HOTFIX_RELEASE, HOTFIX_BACKPORT, RELEASE_CUT,
RELEASE_BACKPORT, OTHER_MERGE

usage:
  $ hupy get current-commit-type""".format(DOC))
