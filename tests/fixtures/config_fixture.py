"""
config_fixture.py

shared HupyConfigFile fixture: loads the base config from the shipped
``.hupy.config.jsonc`` asset, deep-merges caller-supplied overrides
into it, and schema-validates the result; replaces constructing
HupyConfigFile straight from partial kwargs, which relied on field
defaults the schema doesn't provide
"""

import json5

from hupy.config.config_file import HupyConfigFile
from hupy.config.config_file_path import DEFAULT_CONFIG_ASSET

__all__ = ("CONFIG_FIXTURE_PATH", "load_config_fixture")

# constants  ###################################################################

CONFIG_FIXTURE_PATH = DEFAULT_CONFIG_ASSET


# helpers  ######################################################################


def _deep_merge(base, overrides):
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# Public API  ##################################################################


def load_config_fixture(overrides=None):
    """
    load the shared config fixture, deep-merging ``overrides`` into it
    before schema validation.


    :param overrides: partial config values to merge over the fixture,
            nested dicts merged key-by-key rather than replaced wholesale
    :type overrides: dict or None
    :return: the merged, validated configuration
    :rtype: HupyConfigFile
    """
    base = json5.loads(CONFIG_FIXTURE_PATH.read_text())
    merged = _deep_merge(base, overrides or {})
    return HupyConfigFile.model_validate(merged)
