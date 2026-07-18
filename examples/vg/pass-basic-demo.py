#!/usr/bin/env python3
"""
pass-basic-demo.py

demo: version file committed with a line matching the configured
pattern, whose one capture group holds the version string
expected result: PASS, "1.2.3" grepped
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_vg


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(version_content="1.2.3\n")


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tversion file committed, line matches configured pattern")
    print('expected:\tPASS, "1.2.3" grepped')
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
