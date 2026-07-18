#!/usr/bin/env python3
"""
fail-unconfigured-demo.py

demo: `version_file` (and `version_line_pattern`) left empty in the
HUPy config, VerGrep's default, unconfigured state
expected result: fail, empty string returned
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_vg

_VERSION_CONTENT = "1.2.3\n"


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(
        version_file="", version_line_pattern="", version_content=None
    )


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tVerGrep left unconfigured (empty version_file/pattern)")
    print("expected:\tFAIL, empty string returned")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("VG", "="))
    version_1 = run_vg(demo_repo_1)
    print()
    print(gen_comment_banner_centered("grepped version", "-"))
    print("{!r}".format(version_1))
    print()

    print(gen_comment_banner_centered("VG w/ -vvv", "="))
    version_2 = run_vg(demo_repo_2, verbosity=4)
    print()
    print(gen_comment_banner_centered("grepped version", "-"))
    print("{!r}".format(version_2))


if __name__ == "__main__":
    main()
