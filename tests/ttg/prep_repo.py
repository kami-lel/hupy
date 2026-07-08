"""
prep_repo.py

prepare temporary git repositories that reproduce the TTG (triage
tag gating) commit-type buckets, for reuse by unit tests and by the
``examples/ttg`` demo scripts
"""

import shutil
import tempfile
from argparse import ArgumentParser
from pathlib import Path

import git

from hupy.commit_type import DEV_BRANCH, MAIN_BRANCH

_TESTEE_ROOT = Path(__file__).parent.parent / "testee"
_BUNDLE_PATH = _TESTEE_ROOT / "default_repo.bundle"
_FIXTURES_ROOT = _TESTEE_ROOT / "ttg"

COMMIT_BUCKETS = (
    "non_merge_commit",
    "regular_merge",
    "feature_finish",
    "version_release",
)

SCENARIOS = (
    "non_merge_commit",
    "irrelevant_merge",
    "feature_finish_fail",
    "feature_finish_pass",
    "version_release_fail",
    "version_release_pass",
)


# helpers  #####################################################################


def _commit_fixture(repo_dir, filename, fixture_name):
    src = str(_FIXTURES_ROOT / fixture_name)
    dst = str(Path(repo_dir) / filename)
    shutil.copyfile(src, dst)
    repo = git.Repo(str(repo_dir))
    repo.index.add([filename])
    repo.index.commit("add {}".format(filename))


def _stage_fixture(repo_dir, filename, fixture_name):
    src = str(_FIXTURES_ROOT / fixture_name)
    dst = str(Path(repo_dir) / filename)
    shutil.copyfile(src, dst)
    repo = git.Repo(str(repo_dir))
    repo.index.add([filename])


def _setup_non_merge_commit(repo_dir, files):
    # regular commit in progress (no MERGE_HEAD): TTG must skip
    # regardless of the TT tier(s) staged here
    for filename, fixture_name in files.items():
        _stage_fixture(repo_dir, filename, fixture_name)


def _setup_regular_merge(repo_dir, files):
    # merge between two unrelated, non-protected branches: TTG must
    # skip regardless of commit type detail
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", "hotfix")
    for filename, fixture_name in files.items():
        _commit_fixture(repo_dir, filename, fixture_name)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.checkout("-q", "-b", "release")
    _commit_fixture(repo_dir, "release.py", "irrelevant_merge_release.py")
    repo.git.merge("--no-commit", "--no-ff", "hotfix")


def _setup_feature_finish(repo_dir, files):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _commit_fixture(repo_dir, "develop.py", "feature_finish_develop.py")
    repo.git.checkout("-q", "-b", "add-user-authentication")
    for filename, fixture_name in files.items():
        _commit_fixture(repo_dir, filename, fixture_name)
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "add-user-authentication")


def _setup_version_release(repo_dir, files):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    for filename, fixture_name in files.items():
        _commit_fixture(repo_dir, filename, fixture_name)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", DEV_BRANCH)


_BUCKET_SETUP_FUNCS = {
    "non_merge_commit": _setup_non_merge_commit,
    "regular_merge": _setup_regular_merge,
    "feature_finish": _setup_feature_finish,
    "version_release": _setup_version_release,
}

# legacy scenario -> (bucket, default files) presets, kept so the
# ``examples/ttg`` bash demos and the CLI below keep working unchanged.
# each preset mirrors the most file-and-tag-heavy unit test case for
# its bucket (see tests/ttg/ttg-tt_gating_*_test.py)
_LEGACY_SCENARIO_PRESETS = {
    "non_merge_commit": (
        "non_merge_commit",
        {"a.py": "tt_loud_only.py", "b.py": "tt_none.py"},
    ),
    "irrelevant_merge": (
        "regular_merge",
        {"a.py": "tt_loud_only.py", "b.py": "tt_none.py"},
    ),
    "feature_finish_fail": (
        "feature_finish",
        {
            "a.py": "tt_loud_only.py",
            "b.py": "tt_2loud.py",
            "c.py": "tt_quiet_only.py",
        },
    ),
    "feature_finish_pass": (
        "feature_finish",
        {"a.py": "tt_steady_only.py", "b.py": "tt_quiet_only.py"},
    ),
    "version_release_fail": (
        "version_release",
        {
            "a.py": "tt_loud_only.py",
            "b.py": "tt_1loud_2steady.py",
            "c.py": "tt_quiet_only.py",
        },
    ),
    "version_release_pass": (
        "version_release",
        {"a.py": "tt_quiet_only.py", "b.py": "tt_quiet_only.py"},
    ),
}


# Public API  ##################################################################


def prepare_repo_with_files(dest_dir, commit_bucket, files):
    """
    prepare a temporary repository for one of the TTG commit-type
    buckets, staging/committing an arbitrary file manifest.


    :param dest_dir: destination directory for the cloned repo;
            must not already exist, or be empty if it does
    :type dest_dir: str
    :param commit_bucket: commit-type bucket, one of ``COMMIT_BUCKETS``
    :type commit_bucket: str
    :param files: mapping of filename to fixture file name (resolved
            under ``tests/testee/ttg``); each entry is staged or
            committed according to ``commit_bucket``'s scaffold
    :type files: dict
    :raises ValueError: if ``commit_bucket`` is not a known bucket
    :return: path to the prepared repository
    :rtype: str
    """
    if commit_bucket not in _BUCKET_SETUP_FUNCS:
        raise ValueError("unknown commit bucket: {}".format(commit_bucket))

    git.Repo.clone_from(str(_BUNDLE_PATH), str(dest_dir), branch=MAIN_BRANCH)
    _BUCKET_SETUP_FUNCS[commit_bucket](dest_dir, files)
    return str(dest_dir)


def prepare_repo(dest_dir, scenario):
    """
    prepare a temporary repository for one of the legacy named TTG
    scenarios; kept for the ``examples/ttg`` demo scripts.


    :param dest_dir: destination directory for the cloned repo;
            must not already exist, or be empty if it does
    :type dest_dir: str
    :param scenario: scenario name, one of ``SCENARIOS``
    :type scenario: str
    :raises ValueError: if ``scenario`` is not a known scenario name
    :return: path to the prepared repository
    :rtype: str
    """
    if scenario not in _LEGACY_SCENARIO_PRESETS:
        raise ValueError("unknown scenario: {}".format(scenario))

    commit_bucket, files = _LEGACY_SCENARIO_PRESETS[scenario]
    return prepare_repo_with_files(dest_dir, commit_bucket, files)


def _main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        required=True,
        choices=SCENARIOS,
        help="TTG scenario to prepare",
    )
    parser.add_argument(
        "--dest",
        default=None,
        help="destination directory; a fresh temp dir is used if omitted",
    )
    args = parser.parse_args()

    dest_dir = args.dest or tempfile.mkdtemp(prefix="ttg_demo_")
    prepare_repo(dest_dir, args.scenario)
    print(dest_dir)


if __name__ == "__main__":
    _main()
