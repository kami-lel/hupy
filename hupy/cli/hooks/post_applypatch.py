"""
post_applypatch.py

define the post-applypatch stage's identity, run by the generic hook
stage runner in ``cli_hook.py``
"""

# constants  ###################################################################
HOOK_NAME = "post-applypatch"
DOC = "run post-applypatch stage hooks"

