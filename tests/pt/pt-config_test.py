"""
pt-config_test.py

tests for the PT config schema (`_Pt`, `_PaperTrail`) in
`config_file.py`: defaults, strict fields, and `allow_commit_types`
name parsing
"""

import pydantic
import pytest

from config_fixture import load_config_fixture

from hupy.cbm.commit_type import CommitType

# auxiliaries  #################################################################


def _load(pt):
    """
    :return: the PT config section after merging ``pt`` over the fixture
    :rtype: _Pt
    """
    return load_config_fixture(overrides={"pt": pt}).pt


def _load_allow(names):
    """
    :return: parsed ``allow_commit_types`` of a single entry
    :rtype: CommitType
    """
    pt = _load({"trails": [{"glob": "*.md", "allow_commit_types": names}]})
    return pt.trails[0].allow_commit_types


# tests  ########################################################################


class TestPtConfigDefaults:
    def test_shipped_config_has_no_paper_trail(self):
        assert load_config_fixture().pt.trails == []

    def test_shipped_config_is_enabled(self):
        assert load_config_fixture().pt.is_disabled is False


class TestPaperTrailEntry:
    def test_glob_only_entry_uses_defaults(self):
        entry = _load({"trails": [{"glob": "*.md"}]}).trails[0]
        assert entry.glob == "*.md"
        assert entry.allow_commit_types == CommitType(0)
        assert entry.remark == ""

    def test_remark_is_kept(self):
        entry = _load({"trails": [{"glob": "*.md", "remark": "docs"}]})
        assert entry.trails[0].remark == "docs"

    def test_missing_glob_is_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            _load({"trails": [{"remark": "no glob"}]})

    def test_unknown_field_is_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            _load({"trails": [{"glob": "*.md", "bogus": 1}]})

    def test_unknown_pt_field_is_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            _load({"bogus": 1})


class TestAllowCommitTypesParsing:
    def test_single_name(self):
        assert _load_allow(["FEATURE_LANDING"]) == CommitType.FEATURE_LANDING

    def test_several_names_merge_into_union(self):
        assert _load_allow(["FEATURE_LANDING", "VERSION_RELEASE"]) == (
            CommitType.FEATURE_LANDING | CommitType.VERSION_RELEASE
        )

    def test_empty_list_is_no_filter(self):
        assert _load_allow([]) == CommitType(0)

    def test_illegal_name_only_is_skipped(self):
        assert _load_allow(["NOT_A_TYPE"]) == CommitType(0)

    def test_legal_name_survives_beside_illegal_name(self):
        assert _load_allow(["NOT_A_TYPE", "CATCH_UP"]) == CommitType.CATCH_UP

    @pytest.mark.parametrize(
        "member", [m for m in CommitType if m.name is not None]
    )
    def test_every_commit_type_member_name_parses(self, member):
        assert _load_allow([member.name]) == member

    @pytest.mark.parametrize(
        "name", ["MERGE", "RELEASE", "BACKPORT", "INTEGRATION"]
    )
    def test_merge_category_name_parses(self, name):
        assert _load_allow([name]) == CommitType[name]
