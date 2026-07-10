"""
state_file_path.py

resolve the path of the HUPy state file (``hupy-state.json``) inside
a repo's ``.git`` directory
"""

import pathlib

__all__ = ("STATE_FILENAME", "get_state_file_path")


# constants  ###################################################################


STATE_FILENAME = "hupy-state.json"


# Public API  ##################################################################
def get_state_file_path(repo):
    """
    resolve the path of the HUPy state file (``hupy-state.json``)
    inside ``repo``'s ``.git`` directory


    :param repo: git repository object
    :type repo: git.Repo
    :return: path to the HUPy state file
    :rtype: pathlib.Path
    """
    return pathlib.Path(repo.git_dir) / STATE_FILENAME
