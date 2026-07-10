"""
report_tt.py

render and log gated triage tag findings
"""

import re
import sys

from hupy.ttg import TTG_LOGGER_NAME
from hupy.kamilog import AnsiRenderer, getLogger, gen_comment_banner_centered
from .detect_tt import _TT_PATTERN

# logger  ######################################################################
logger = getLogger(TTG_LOGGER_NAME)


# Public API  ##################################################################


def report_gated_tags(filtered_results):
    """
    log gated triage tag findings and abort the commit.


    :param filtered_results: staged file path -> gated
            ``(tag, line, line_no)`` tuples
    :type filtered_results: dict
    """
    logger.fail("gated Triage Tags found")
    renderer = AnsiRenderer(sys.stdout)
    msg_lines = [""]
    for file_path, results in filtered_results.items():
        msg_lines.append(gen_comment_banner_centered(file_path, "-"))
        line_no_width = max(len(str(line_no)) for _, _, line_no in results)
        for _, line, line_no in results:
            line_no_str = renderer.color_grey(str(line_no).rjust(line_no_width))
            stripped_line = line.strip()
            match = re.search(_TT_PATTERN, stripped_line)
            if match:
                colored_tag = renderer.color_triage_tag(match.group(1))
                stripped_line = (
                    stripped_line[: match.start()]
                    + colored_tag
                    + stripped_line[match.end() :]
                )
            msg_lines.append(line_no_str + " " + stripped_line)
    logger.info("\n".join(msg_lines))
    raise SystemExit(1)
