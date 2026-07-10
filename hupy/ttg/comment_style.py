"""
comment_style.py

map file extensions to the comment-leader token used when
detecting triage tags by file type
"""

import pathlib

# constants  ###################################################################

_EXTENSION_TO_COMMENT_PREFIX = {
    # C-style line comment
    ".c": "//",
    ".h": "//",
    ".cpp": "//",
    ".hpp": "//",
    ".cc": "//",
    ".cxx": "//",
    ".hh": "//",
    ".java": "//",
    ".js": "//",
    ".jsx": "//",
    ".ts": "//",
    ".tsx": "//",
    ".go": "//",
    ".rs": "//",
    ".swift": "//",
    ".kt": "//",
    ".cs": "//",
    # hash comment
    ".py": "#",
    ".sh": "#",
    ".bash": "#",
    ".rb": "#",
    ".yaml": "#",
    ".yml": "#",
    ".toml": "#",
    ".pl": "#",
    ".r": "#",
    # HTML-style comment
    ".html": "<!--",
    ".htm": "<!--",
    ".xml": "<!--",
    ".md": "<!--",
    ".vue": "<!--",
    ".svg": "<!--",
}


# Public API  ##################################################################


def get_comment_prefix_for_file(file_path):
    """
    look up the comment-leader token for a file's extension.


    :param file_path: path to the file, real or relative
    :type file_path: str
    :return: comment-leader token (eg ``"//"``, ``"#"``, ``"<!--"``),
            or ``None`` when the extension is unmapped
    :rtype: str or None
    """
    suffix = pathlib.Path(file_path).suffix.lower()
    return _EXTENSION_TO_COMMENT_PREFIX.get(suffix)
