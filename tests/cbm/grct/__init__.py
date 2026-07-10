"""
__init__.py

repo-building helpers for `get_current_commit_type.py` (grct) tests.
Realistic merge states are built via `prepare_merge_repo`, on top of
the shared `prep_repo` fixture builder (tests/fixtures/prep_repo.py),
rather than hand-rolling checkout/commit/merge here. Only the cases
`prep_repo`'s canned buckets don't cover (a MERGE_HEAD sha that's no
longer a branch tip, a detached HEAD) still need a raw clone plus
direct git pokes.
"""

import sys
from pathlib import Path

import git

_PKG_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent.parent

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from prep_repo import prepare_repo_with_files  # noqa: E402

_DEFAULT_FILES = {"a.py": "tt_none.py"}


# Public API  ##################################################################


def prepare_merge_repo(dest_dir, commit_bucket, files=None):
    """
    prepare a repo with a real in-progress merge for one of
    `prep_repo.COMMIT_BUCKETS`, returning a `git.Repo`.
    """
    prepare_repo_with_files(dest_dir, commit_bucket, files or _DEFAULT_FILES)
    return git.Repo(str(dest_dir))


def clone_repo(dest_dir):
    """clone the plain default_repo bundle, no merge in progress."""
    prepare_repo_with_files(dest_dir, "non_merge_commit", _DEFAULT_FILES)
    repo = git.Repo(str(dest_dir))
    repo.git.reset("-q", "--hard", "HEAD")  # drop the staged default file
    return repo


def sha_of(repo, ref):
    """get the sha of a ref in the repo."""
    return repo.git.rev_parse(ref)


def write_merge_head(repo_dir, sha):
    """overwrite MERGE_HEAD with an arbitrary sha."""
    (Path(repo_dir) / ".git" / "MERGE_HEAD").write_text(sha + "\n")


def commit_file(repo_dir, name):
    """create a commit adding a file named ``name`` in repo_dir."""
    repo = git.Repo(str(repo_dir))
    (Path(repo_dir) / name).write_text(name)
    repo.index.add([name])
    repo.index.commit(name)
