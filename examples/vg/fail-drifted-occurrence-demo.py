#!/usr/bin/env python3
"""
fail-drifted-occurrence-demo.py

demo: the canonical version bumped in `pyproject.toml`, but a README
badge was never updated to match
expected result: FAIL, SystemExit(1) raised
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
    "pyproject.toml": 'version = "2.0.0"\n',
    "README.md": "badge: version-1.2.3-blue\n",
}


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tREADME badge left behind after a version bump")
    print("expected:\tFAIL, SystemExit(1) raised")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo = prepare_uniformity_demo_repo(_OCCURRENCES, _FILES)

    print(gen_comment_banner_centered("Version Uniformity w/ -vvv", "="))
    try:
        run_uniformity(demo_repo, verbosity=4)
        print()
        print("no SystemExit raised (unexpected)")
    except SystemExit as exc:
        print()
        print("SystemExit raised, code={!r}".format(exc.code))


if __name__ == "__main__":
    main()
