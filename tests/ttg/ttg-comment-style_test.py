"""
ttg-comment-style_test.py

tests for extension-to-comment-prefix lookup in `comment_style.py`
"""

from hupy.ttg.comment_style import get_comment_prefix_for_file


# tests  ########################################################################


class TestGetCommentPrefixForFile:
    def test_c_style_extension(self):
        assert get_comment_prefix_for_file("main.cpp") == "//"

    def test_hash_style_extension(self):
        assert get_comment_prefix_for_file("script.py") == "#"

    def test_html_style_extension(self):
        assert get_comment_prefix_for_file("page.html") == "<!--"

    def test_case_insensitive_extension(self):
        assert get_comment_prefix_for_file("Main.CPP") == "//"

    def test_unmapped_extension_returns_none(self):
        assert get_comment_prefix_for_file("data.bin") is None

    def test_no_extension_returns_none(self):
        assert get_comment_prefix_for_file("README") is None
