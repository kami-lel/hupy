"""
detect_tt.py

triage tag detection in staged git diffs
"""

import re
import subprocess

from hupy.kamilog import getLogger
from hupy.ttg import TTG_LOGGER_NAME
from .comment_style import get_comment_prefix_for_file
from .triage_tag_type import TriageTagType

# logger  ######################################################################
logger = getLogger(TTG_LOGGER_NAME)


# constants  ###################################################################

_HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


# Public API  ##################################################################


def detect_triage_tags_in_staged_file(
    file_path, repo_root=None, disable_tt_detect_by_type=False
):
    """
    detect triage tags in staged additions.

    scan git staged diff for added lines containing triage tags
    (TODO, FIXME, HACK, BUG) in all three tiers (Loud, Steady,
    Quiet). when ``disable_tt_detect_by_type`` is ``False``, a tag
    only counts when it follows the comment-leader token expected
    for ``file_path``'s extension (eg ``//`` for ``.cpp``, ``#`` for
    ``.py``); files with an unmapped or missing extension fall back
    to matching the tag anywhere in the line.


    :param file_path: path to the file to scan, relative to
            ``repo_root`` when given
    :type file_path: str
    :param repo_root: path to the git repository or any of its
            subdirectories; defaults to the current directory
    :type repo_root: str or None
    :param disable_tt_detect_by_type: when ``True``, ignore the
            file's extension and match tags anywhere in the line
    :type disable_tt_detect_by_type: bool
    :return: list of tuples ``(tag_member, line, line_no)`` for
            detected tags
    :rtype: list
    """
    logger.debug("search TT in: " + str(file_path))

    comment_prefix = (
        None
        if disable_tt_detect_by_type
        else get_comment_prefix_for_file(file_path)
    )

    try:
        diff_output = subprocess.check_output(
            ("git", "diff", "--cached", "--", file_path),
            text=True,
            stderr=subprocess.PIPE,
            cwd=repo_root,
        )
    except subprocess.CalledProcessError as e:
        logger.critical("unable to get git diff for file: %s", file_path)
        raise SystemExit(1) from e

    results = []
    line_no = 0

    for line in diff_output.split("\n"):
        hunk_match = _HUNK_HEADER_PATTERN.match(line)
        if hunk_match:
            line_no = int(hunk_match.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            added_line = line[1:]
            tag_member = TriageTagType.find_first_in_line(
                added_line, comment_prefix
            )
            if tag_member:
                results.append((tag_member, added_line, line_no))
            line_no += 1
        elif line.startswith(" "):
            line_no += 1

    return results
