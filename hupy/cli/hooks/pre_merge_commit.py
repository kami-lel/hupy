"""
pre_merge_commit.py

define the pre-merge-commit stage's identity, run by the generic hook
stage runner in ``cli_hook.py``
"""

# constants  ###################################################################
HOOK_NAME = "pre-merge-commit"
DOC = "run pre-merge-commit stage hooks"

