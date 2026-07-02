"""
prep_repo.py

prepare temporary git repositories that reproduce the six TTG
(triage tag gating) commit scenarios, for reuse by unit tests and
by the ``examples/ttg`` demo scripts
"""

import shutil
import tempfile
from argparse import ArgumentParser
from pathlib import Path

import git

from hupy.ttg.commit_type import DEV_BRANCH, MAIN_BRANCH

_TESTEE_ROOT = Path(__file__).parent.parent / "testee"
_BUNDLE_PATH = _TESTEE_ROOT / "default_repo.bundle"
_FIXTURES_ROOT = _TESTEE_ROOT / "ttg"

SCENARIOS = (
    "non_merge_commit",
    "irrelevant_merge",
    "feature_finish_loud",
    "feature_finish_steady_only",
    "version_release_steady",
    "version_release_quiet_only",
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


def _setup_non_merge_commit(repo_dir):
    # regular commit in progress (no MERGE_HEAD): TTG must skip
    # regardless of the TT tier staged here
    _stage_fixture(repo_dir, "feature.py", "non_merge_commit_feature.py")


def _setup_irrelevant_merge(repo_dir):
    # merge between two unrelated, non-protected branches: TTG must
    # skip regardless of commit type detail
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", "hotfix")
    _commit_fixture(repo_dir, "hotfix.py", "irrelevant_merge_hotfix.py")
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.checkout("-q", "-b", "release")
    _commit_fixture(repo_dir, "release.py", "irrelevant_merge_release.py")
    repo.git.merge("--no-commit", "--no-ff", "hotfix")


def _setup_feature_finish(repo_dir, fixture_name):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _commit_fixture(repo_dir, "develop.py", "feature_finish_develop.py")
    repo.git.checkout("-q", "-b", "feature/x")
    _commit_fixture(repo_dir, "feature.py", fixture_name)
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "feature/x")


def _setup_version_release(repo_dir, fixture_name):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _commit_fixture(repo_dir, "release.py", fixture_name)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", DEV_BRANCH)


_SCENARIO_SETUP_FUNCS = {
    "non_merge_commit": _setup_non_merge_commit,
    "irrelevant_merge": _setup_irrelevant_merge,
    "feature_finish_loud": (
        lambda repo_dir: _setup_feature_finish(
            repo_dir, "feature_finish_loud.py"
        )
    ),
    "feature_finish_steady_only": (
        lambda repo_dir: _setup_feature_finish(
            repo_dir, "feature_finish_steady_only.py"
        )
    ),
    "version_release_steady": (
        lambda repo_dir: _setup_version_release(
            repo_dir, "version_release_steady.py"
        )
    ),
    "version_release_quiet_only": (
        lambda repo_dir: _setup_version_release(
            repo_dir, "version_release_quiet_only.py"
        )
    ),
}


# Public API  ##################################################################


def prepare_repo(dest_dir, scenario):
    """
    prepare a temporary repository for one of the TTG scenarios.


    :param dest_dir: destination directory for the cloned repo;
            must not already exist, or be empty if it does
    :type dest_dir: str
    :param scenario: scenario name, one of ``SCENARIOS``
    :type scenario: str
    :raises ValueError: if ``scenario`` is not a known scenario name
    :return: path to the prepared repository
    :rtype: str
    """
    if scenario not in _SCENARIO_SETUP_FUNCS:
        raise ValueError("unknown scenario: {}".format(scenario))

    git.Repo.clone_from(str(_BUNDLE_PATH), str(dest_dir), branch=MAIN_BRANCH)
    _SCENARIO_SETUP_FUNCS[scenario](dest_dir)
    return str(dest_dir)


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
