"""
names_by_demand.py

decide which git hook names actually need an installed stub
"""

__all__ = ("get_hook_names_by_demand",)

# Public API  ##################################################################


def get_hook_names_by_demand():
    """
    :return: hook names that should have an installed stub
    :rtype: list[str]
    """
    return [
        "pre-commit",
        "prepare-commit-msg",
        "post-commit",
    ]
