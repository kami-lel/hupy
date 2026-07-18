#!/usr/bin/env python3
"""
fail-no-capture-group-demo.py

demo: version file has a matching line, but the configured pattern
carries no capture group to grep the version out of it
expected result: fail, empty string returned
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_vg

_PATTERN_NO_GROUP = r"\d+\.\d+\.\d+"


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(
        version_line_pattern=_PATTERN_NO_GROUP, version_content="1.2.3\n"
    )


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tmatching line found, but pattern has no capture group")
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
