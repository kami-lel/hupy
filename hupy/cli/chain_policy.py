"""
chain_policy.py

decide chain-session lifecycle: which git process owns the current
chain, whether a stage closes that chain, and whether an amend will
tack a ``post-rewrite`` onto the tail
"""

__all__ = (
    "TERMINAL_ALWAYS",
    "adopt_session",
    "detect_amend",
    "is_chain_terminal",
)


# constants  ###################################################################

# multi-stage chains whose named stage is always the last to run
_CHAIN_TERMINALS = frozenset(
    {
        "post-merge",  # merge / pull chain tail
        "post-applypatch",  # patch-apply chain tail
        "post-rewrite",  # amend / rebase chain tail
    }
)

# one-stage chains: each fires alone, so each is its own tail
_STANDALONE_HOOKS = frozenset(
    {
        "pre-auto-gc",
        "post-index-change",
        "sendemail-validate",
        "fsmonitor-watchman",
        "post-checkout",
        "pre-push",
    }
)

# every stage that closes its chain unconditionally
TERMINAL_ALWAYS = _CHAIN_TERMINALS | _STANDALONE_HOOKS


# Public API  ##################################################################


def adopt_session(session, ppid):
    """
    ensure ``session`` is owned by ``ppid``, the current stage's git
    process; a differing owner (a fresh chain, or a stale one left by an
    aborted chain) is reclaimed by re-adopting from idle defaults


    :param session: the chain session to adopt in place
    :type session: hupy.state.state_file.ChainSession
    :param ppid: the git process id owning this stage (``os.getppid()``)
    :type ppid: int
    :return: whether a fresh chain was begun
    :rtype: bool
    """
    if session.chain_ppid == ppid:
        return False  # same git process, chain continues

    session.reset()
    session.chain_ppid = ppid
    return True


def is_chain_terminal(hook_name, session):
    """
    report whether ``hook_name`` is the last stage of its chain, so the
    single per-chain DONE belongs here


    :param hook_name: the running stage's ``HOOK_NAME``
    :type hook_name: str
    :param session: the current chain session
    :type session: hupy.state.state_file.ChainSession
    :return: whether this stage closes the chain
    :rtype: bool
    """
    if hook_name in TERMINAL_ALWAYS:
        return True

    # post-commit always runs, but yields to post-rewrite on an amend
    if hook_name == "post-commit":
        return not session.expect_post_rewrite

    return False


def detect_amend(hook_args):
    """
    read git's prepare-commit-msg args ``<msg_file> <source> [<sha>]``:
    an amend (also ``-c`` / ``-C``) sets ``source`` to ``commit``,
    signalling that a ``post-rewrite`` will close the chain


    :param hook_args: raw args forwarded to the prepare-commit-msg stage
    :type hook_args: list[str]
    :return: whether a trailing post-rewrite is expected
    :rtype: bool
    """
    # FIXME `-c`/`-C` without `--amend` also gives source `commit` yet
    # spawns no post-rewrite, so this over-predicts for that rare case
    return len(hook_args) >= 2 and hook_args[1] == "commit"
