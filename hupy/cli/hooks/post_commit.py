"""
post_commit.py

define the post-commit stage's identity, run by the generic hook
stage runner in ``cli_hook.py``; the chain-close reset now lives in
``cli_hook.py``, since ``post-commit`` yields to ``post-rewrite`` on
an amend
"""

# constants  ###################################################################
HOOK_NAME = "post-commit"
