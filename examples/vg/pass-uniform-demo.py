#!/usr/bin/env python3
"""
pass-uniform-demo.py

demo: every configured occurrence carries the same version as the
canonical entry
expected result: PASS, no exception raised
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_uniformity_demo_repo, run_uniformity

_OCCURRENCES = [
    {
        "remark": "canonical version",
        "file": "pyproject.toml",
        "glob": r'version = "(.*)"',
    },
    {
        "remark": "README badge",
        "file": "README.md",
        "glob": r"version-(\S+)-blue",
    },
]
_FILES = {
    "pyproject.toml": 'version = "1.2.3"\n',
    "README.md": "badge: version-1.2.3-blue\n",
}


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tevery occurrence carries the same version")
    print("expected:\tPASS, no exception raised")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo = prepare_uniformity_demo_repo(_OCCURRENCES, _FILES)

    print(gen_comment_banner_centered("Version Uniformity w/ -vvv", "="))
    run_uniformity(demo_repo, verbosity=4)
    print()
    print("no SystemExit raised")


if __name__ == "__main__":
    main()
