"""
prep_repo.py

prepare temporary git repositories that reproduce CBM commit-type
buckets, for reuse by unit tests and by the ``examples/ttg`` and
``examples/pch`` demo scripts; shared fixture-building CLI for all of
``tests/``
"""

import os
import shutil
import tempfile
from argparse import ArgumentParser
from pathlib import Path

import git

from hupy.config.config_file_path import DEFAULT_CONFIG_ASSET

MAIN_BRANCH = "main"
DEV_BRANCH = "dev"

_FIXTURES_DIR = Path(__file__).parent
_BUNDLE_PATH = _FIXTURES_DIR / "default_repo.bundle"
_FIXTURES_ROOT = _FIXTURES_DIR.parent / "ttg" / "fixtures"

COMMIT_BUCKETS = (
    "non_merge_commit",
    "regular_merge",
    "feature_landing",
    "version_release",
)

SCENARIOS = (
    "non_merge_commit",
    "irrelevant_merge",
    "feature_landing_fail",
    "feature_landing_pass",
    "version_release_fail",
    "version_release_pass",
)

# demo-only repo scaffolds with no TT-tag file manifest, used by
# ``examples/pch`` demo scripts, not by unit tests: the first six are
# CBM merge types PCH's header generators cover but that have no
# dedicated ``tests/pch/`` file yet; the ``release_*`` ones below
# exercise the Version Release header's release-type/bump-prefix
# wording (``examples/pch/vr-*-demo.py``)
DEMO_BUCKETS = (
    "sync_backport",
    "catch_up",
    "hotfix_release",
    "hotfix_backport",
    "release_cut",
    "release_backport",
    "release_fail_parse",
    "release_minor_prototype",
    "release_alpha",
    "release_beta",
    "release_rc",
    "release_major_stable",
    "release_minor_pre_alpha",
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


def _bump_source_branch_version(repo_dir, version):
    # give the branch about to be merged in a version distinct from
    # main's 1.2.3, so demos exercise a real version diff between the
    # current and coming branch instead of both sides reading
    # identically
    _write_and_commit(
        repo_dir,
        "setup.cfg",
        "[metadata]\nname = default_repo\nversion = {}\n".format(version),
    )


def _setup_feature_landing(repo_dir, files):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _commit_fixture(repo_dir, "develop.py", "feature_landing_develop.py")
    repo.git.checkout("-q", "-b", "add-user-authentication")
    _bump_source_branch_version(repo_dir, "1.3.0")
    for filename, fixture_name in files.items():
        _commit_fixture(repo_dir, filename, fixture_name)
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "add-user-authentication")


def _setup_version_release(repo_dir, files):
    # bumps a major version (main's 1.2.3 -> 2.0.0) so this scenario
    # is ready to show a "Major " bump prefix once pch wires
    # _gen_version_release_header through _gen_bumped_version_header
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _bump_source_branch_version(repo_dir, "2.0.0")
    for filename, fixture_name in files.items():
        _commit_fixture(repo_dir, filename, fixture_name)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", DEV_BRANCH)


def _chdir_into_repo(repo_dir):
    # HUPy resolves ``vg.version_file`` against the process cwd,
    # so tests must chdir into the prepared repo for the bundled
    # ``setup.cfg`` to be found; not restored after the test, since
    # each test starts a fresh scenario repo anyway
    os.chdir(str(repo_dir))


def _write_config_file(repo_dir):
    # the bundle no longer carries a committed HUPy config file, so
    # write the shipped default config straight onto disk, untracked,
    # for ``load_hupy_config`` to read
    shutil.copyfile(
        DEFAULT_CONFIG_ASSET, Path(repo_dir) / ".hupy.config.jsonc"
    )


def _write_and_commit(repo_dir, filename, content):
    path = Path(repo_dir) / filename
    path.write_text(content)
    repo = git.Repo(str(repo_dir))
    repo.index.add([filename])
    repo.index.commit("add {}".format(filename))


def _bump_dev_own_version(repo_dir):
    # simulate dev's own in-progress next-cycle version, distinct from
    # whatever the backport source branch carries; demo buckets that
    # exercise `grep_source_branch_version` call this on DEV_BRANCH
    # right after branching it, before the source branch is built, so
    # a demo that wrongly reads DEV's (target's) version instead of
    # the source branch's is visibly wrong rather than coincidentally
    # right
    _write_and_commit(
        repo_dir,
        "setup.cfg",
        "[metadata]\nname = default_repo\nversion = 1.3.0-dev\n",
    )


def _setup_sync_backport(repo_dir):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _bump_dev_own_version(repo_dir)
    repo.git.checkout("-q", MAIN_BRANCH)
    _write_and_commit(repo_dir, "hotdoc.py", "# patched directly on main\n")
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", MAIN_BRANCH)


def _setup_catch_up(repo_dir):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    repo.git.checkout("-q", "-b", "add-payment-gateway")
    repo.git.checkout("-q", DEV_BRANCH)
    _write_and_commit(repo_dir, "notify.py", "# new work landed on dev\n")
    repo.git.checkout("-q", "add-payment-gateway")
    repo.git.merge("--no-commit", "--no-ff", DEV_BRANCH)


def _setup_hotfix_release(repo_dir):
    # bumps a patch version (main's 1.2.3 -> 1.2.4) so this demo shows
    # a "Patch " bump prefix
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", "hotfix/fix-login-crash")
    _write_and_commit(repo_dir, "login.py", "# patch login crash\n")
    _bump_source_branch_version(repo_dir, "1.2.4")
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "hotfix/fix-login-crash")


def _setup_hotfix_backport(repo_dir):
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _bump_dev_own_version(repo_dir)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.checkout("-q", "-b", "hotfix/fix-login-crash")
    _write_and_commit(repo_dir, "login.py", "# patch login crash\n")
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "hotfix/fix-login-crash")


def _setup_release_cut(repo_dir):
    # bumps a minor version (main's 1.2.3 -> 1.3.0) so this demo shows
    # a "Minor " bump prefix
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", "release/1.3.0")
    _write_and_commit(repo_dir, "changelog.py", "# freeze for 1.3.0\n")
    _bump_source_branch_version(repo_dir, "1.3.0")
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "release/1.3.0")


def _setup_release_backport(repo_dir):
    # unlike sync/hotfix backport, the source branch's name embeds its
    # own version (release/2.4.0); DEV must not also bump the version
    # line here, or two divergent edits to the same line would leave
    # a real, unresolvable merge conflict rather than an in-progress
    # merge to demo
    repo = git.Repo(str(repo_dir))
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.checkout("-q", "-b", "release/2.4.0")
    _write_and_commit(repo_dir, "changelog.py", "# freeze for 2.4.0\n")
    _write_and_commit(
        repo_dir,
        "setup.cfg",
        "[metadata]\nname = default_repo\nversion = 2.4.0\n",
    )
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", "release/2.4.0")


def _setup_version_release_with_versions(repo_dir, source_version, target_version=None):
    # a dev-into-main in-progress merge with explicit source/target
    # versions, for demoing a specific Version Release header
    # release-type/bump-prefix combination; when target_version is
    # given, main's version is rewritten first, so the comparison
    # isn't pinned to the bundle's default 1.2.3
    repo = git.Repo(str(repo_dir))
    if target_version is not None:
        _bump_source_branch_version(repo_dir, target_version)
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    _bump_source_branch_version(repo_dir, source_version)
    repo.git.checkout("-q", MAIN_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", DEV_BRANCH)


def _setup_release_fail_parse(repo_dir):
    _setup_version_release_with_versions(repo_dir, "v2024.07-rc1")


def _setup_release_minor_prototype(repo_dir):
    _setup_version_release_with_versions(
        repo_dir, "0.4.0", target_version="0.3.0"
    )


def _setup_release_alpha(repo_dir):
    _setup_version_release_with_versions(repo_dir, "1.3.0-alpha.1")


def _setup_release_beta(repo_dir):
    _setup_version_release_with_versions(repo_dir, "1.3.0-beta.1")


def _setup_release_rc(repo_dir):
    _setup_version_release_with_versions(repo_dir, "1.3.0-rc.1")


def _setup_release_major_stable(repo_dir):
    _setup_version_release_with_versions(
        repo_dir, "2.0.0", target_version="1.2.3"
    )


def _setup_release_minor_pre_alpha(repo_dir):
    _setup_version_release_with_versions(
        repo_dir, "0.9.0", target_version="0.8.5"
    )


_BUCKET_SETUP_FUNCS = {
    "non_merge_commit": _setup_non_merge_commit,
    "regular_merge": _setup_regular_merge,
    "feature_landing": _setup_feature_landing,
    "version_release": _setup_version_release,
}

_DEMO_BUCKET_SETUP_FUNCS = {
    "sync_backport": _setup_sync_backport,
    "catch_up": _setup_catch_up,
    "hotfix_release": _setup_hotfix_release,
    "hotfix_backport": _setup_hotfix_backport,
    "release_cut": _setup_release_cut,
    "release_backport": _setup_release_backport,
    "release_fail_parse": _setup_release_fail_parse,
    "release_minor_prototype": _setup_release_minor_prototype,
    "release_alpha": _setup_release_alpha,
    "release_beta": _setup_release_beta,
    "release_rc": _setup_release_rc,
    "release_major_stable": _setup_release_major_stable,
    "release_minor_pre_alpha": _setup_release_minor_pre_alpha,
}

# legacy scenario -> (bucket, default files) presets, kept so the
# ``examples/ttg`` bash demos and the CLI below keep working unchanged.
# each preset mirrors the most file-and-tag-heavy unit test case for
# its bucket (see tests/ttg/ttg-gate_tt_*_test.py)
_LEGACY_SCENARIO_PRESETS = {
    "non_merge_commit": (
        "non_merge_commit",
        {"a.py": "tt_loud_only.py", "b.py": "tt_none.py"},
    ),
    "irrelevant_merge": (
        "regular_merge",
        {"a.py": "tt_loud_only.py", "b.py": "tt_none.py"},
    ),
    "feature_landing_fail": (
        "feature_landing",
        {
            "a.py": "tt_loud_only.py",
            "b.py": "tt_2loud.py",
            "c.py": "tt_quiet_only.py",
        },
    ),
    "feature_landing_pass": (
        "feature_landing",
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
            under ``tests/ttg/fixtures``); each entry is staged or
            committed according to ``commit_bucket``'s scaffold
    :type files: dict
    :raises ValueError: if ``commit_bucket`` is not a known bucket
    :return: path to the prepared repository
    :rtype: str
    """
    if commit_bucket not in _BUCKET_SETUP_FUNCS:
        raise ValueError("unknown commit bucket: {}".format(commit_bucket))

    git.Repo.clone_from(str(_BUNDLE_PATH), str(dest_dir), branch=MAIN_BRANCH)
    _chdir_into_repo(dest_dir)
    _write_config_file(dest_dir)
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


def prepare_demo_repo(dest_dir, demo_bucket):
    """
    prepare a temporary repository for one of the ``examples/pch``
    skip-demo scenarios (CBM merge types PCH does not yet handle).


    :param dest_dir: destination directory for the cloned repo;
            must not already exist, or be empty if it does
    :type dest_dir: str
    :param demo_bucket: demo bucket, one of ``DEMO_BUCKETS``
    :type demo_bucket: str
    :raises ValueError: if ``demo_bucket`` is not a known bucket
    :return: path to the prepared repository
    :rtype: str
    """
    if demo_bucket not in _DEMO_BUCKET_SETUP_FUNCS:
        raise ValueError("unknown demo bucket: {}".format(demo_bucket))

    git.Repo.clone_from(str(_BUNDLE_PATH), str(dest_dir), branch=MAIN_BRANCH)
    _chdir_into_repo(dest_dir)
    _write_config_file(dest_dir)
    _DEMO_BUCKET_SETUP_FUNCS[demo_bucket](dest_dir)
    return str(dest_dir)


def _main():
    parser = ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scenario",
        choices=SCENARIOS,
        help="TTG/PCH scenario to prepare",
    )
    group.add_argument(
        "--demo-bucket",
        choices=DEMO_BUCKETS,
        help="PCH skip-demo bucket to prepare",
    )
    parser.add_argument(
        "--dest",
        default=None,
        help="destination directory; a fresh temp dir is used if omitted",
    )
    args = parser.parse_args()

    dest_dir = args.dest or tempfile.mkdtemp(prefix="repo_prep_")
    if args.scenario:
        prepare_repo(dest_dir, args.scenario)
    else:
        prepare_demo_repo(dest_dir, args.demo_bucket)
    print(dest_dir)


if __name__ == "__main__":
    _main()
