"""
state_file.py

define the HUPy state schema (``hupy-state.json``) as a pydantic
model
"""

from pydantic import BaseModel, Field

__all__ = ("ChainSession", "HupyStateFile")


# data structure  ##############################################################


class ChainSession(BaseModel):
    """
    per-chain session, keyed by the owning git process
    """

    chain_ppid: int | None = None  # git process PID, session key
    expect_post_rewrite: bool = False  # amend/rebase closer will follow

    def is_active(self):
        """
        report whether a chain session is currently adopted
        """
        return self.chain_ppid is not None

    def reset(self):
        """
        forget the current session, back to the idle defaults
        """
        self.chain_ppid = None
        self.expect_post_rewrite = False


class HupyStateFile(BaseModel):
    """
    schema for the HUPy state file (``hupy-state.json``)
    """

    hooks_logger_verbosity: int = 1
    skip_once: set[str] = Field(default_factory=set)
    chain_session: ChainSession = Field(default_factory=ChainSession)

    def reset_for_next_chain(self):
        """
        spend every one-time flag and forget the session, now that the
        chain has finished
        """
        self.skip_once.clear()
        self.chain_session.reset()
