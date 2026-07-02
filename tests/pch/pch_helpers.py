"""
pch_helpers.py

helpers for seeding and inspecting COMMIT_EDITMSG in PCH test scenarios
"""

import shutil
from pathlib import Path


# Public API  ##################################################################


def seed_commit_editmsg_from_merge_msg(repo_dir):
    """
    copy the in-progress merge message into COMMIT_EDITMSG, mirroring
    what git itself does before invoking the commit-msg hook.
    """
    git_dir = Path(repo_dir) / ".git"
    shutil.copyfile(str(git_dir / "MERGE_MSG"), str(git_dir / "COMMIT_EDITMSG"))


def write_commit_editmsg(repo_dir, text):
    """
    write arbitrary ``text`` to COMMIT_EDITMSG.
    """
    path = Path(repo_dir) / ".git" / "COMMIT_EDITMSG"
    path.write_text(text, encoding="utf-8")


def read_commit_editmsg(repo_dir):
    """
    read and return the current COMMIT_EDITMSG content.
    """
    path = Path(repo_dir) / ".git" / "COMMIT_EDITMSG"
    return path.read_text(encoding="utf-8")


def stray_temp_files(repo_dir):
    """
    return any leftover ``commit-msg.*`` atomic-write temp files.
    """
    return list((Path(repo_dir) / ".git").glob("commit-msg.*"))
