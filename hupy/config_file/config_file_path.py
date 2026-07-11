"""
config_file_path.py

resolve the path of the HUPy config file (``.hupy.config.jsonc``) at
a repo's working tree root
"""

import pathlib

__all__ = ("CONFIG_FILENAME", "DEFAULT_CONFIG_ASSET", "get_config_file_path")


# constants  ###################################################################


CONFIG_FILENAME = ".hupy.config.jsonc"

DEFAULT_CONFIG_ASSET = (
    pathlib.Path(__file__).resolve().parent.parent
    / "assets"
    / ".hupy.config.jsonc"
)


# Public API  ##################################################################
def get_config_file_path(repo):
    """
    resolve the path of the HUPy config file (``.hupy.config.jsonc``)
    at ``repo``'s working tree root


    :param repo: git repository object
    :type repo: git.Repo
    :return: path to the HUPy config file
    :rtype: pathlib.Path
    """
    return pathlib.Path(repo.working_tree_dir) / CONFIG_FILENAME
