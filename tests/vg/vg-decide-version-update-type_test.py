"""
vg-decide-version-update-type_test.py

tests for `decide_version_update_type` in `version_bump.py`
"""

from hupy.ver_grep import decide_version_update_type


# tests  ########################################################################


class TestDecideVersionUpdateTypeMajor:
    def test_major_bump_is_x(self):
        assert decide_version_update_type("2.0.0", "1.9.9") == "x"

    def test_major_bump_wins_over_lower_minor_and_patch(self):
        assert decide_version_update_type("2.0.0", "1.9.9") == "x"


class TestDecideVersionUpdateTypeMinor:
    def test_minor_bump_is_y(self):
        assert decide_version_update_type("1.3.0", "1.2.9") == "y"

    def test_minor_bump_requires_same_major(self):
        assert decide_version_update_type("2.1.0", "1.9.0") == "x"


class TestDecideVersionUpdateTypePatch:
    def test_patch_bump_is_z(self):
        assert decide_version_update_type("1.2.4", "1.2.3") == "z"

    def test_patch_bump_requires_same_major_and_minor(self):
        assert decide_version_update_type("1.3.1", "1.2.9") == "y"


class TestDecideVersionUpdateTypeNoUpdate:
    def test_equal_versions_returns_empty(self):
        assert decide_version_update_type("1.2.3", "1.2.3") == ""

    def test_lower_major_returns_empty(self):
        assert decide_version_update_type("1.9.9", "2.0.0") == ""

    def test_same_major_lower_minor_returns_empty(self):
        assert decide_version_update_type("1.2.9", "1.3.0") == ""

    def test_same_major_minor_lower_patch_returns_empty(self):
        assert decide_version_update_type("1.2.3", "1.2.4") == ""

    def test_downgraded_major_with_higher_minor_returns_empty(self):
        # a lower major always loses, even if minor looks like a bump
        assert decide_version_update_type("1.9.9", "2.0.0") == ""


class TestDecideVersionUpdateTypeUnparsable:
    def test_unparsable_coming_version_returns_empty(self):
        assert decide_version_update_type("not-a-version", "1.2.3") == ""

    def test_unparsable_current_version_returns_empty(self):
        assert decide_version_update_type("1.2.3", "not-a-version") == ""

    def test_both_unparsable_returns_empty(self):
        assert decide_version_update_type("x", "y") == ""

    def test_leading_non_digit_prefix_is_unparsable(self):
        # the core pattern is anchored at the start of the string, so
        # a "v" prefix does not parse
        assert decide_version_update_type("v2.0.0", "1.0.0") == ""


class TestDecideVersionUpdateTypeSuffixes:
    def test_prerelease_suffix_on_coming_version_is_ignored(self):
        assert decide_version_update_type("2.0.0-rc1", "1.9.9") == "x"

    def test_build_metadata_suffix_on_current_version_is_ignored(self):
        assert decide_version_update_type("1.3.0", "1.2.3+build5") == "y"
