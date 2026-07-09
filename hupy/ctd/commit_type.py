"""
commit_type.py

commit type flag: categorize git commits by merge strategy
"""

from enum import Flag, auto

__all__ = ("CommitType",)


# TODO make branch names configurable
# TODO support hotfix/release branches

MAIN_BRANCH = "main"
DEV_BRANCH = "dev"


class CommitType(Flag):
	"""
	represent the type of an in-progress git commit with two-level
	hierarchy: level 1 distinguishes merges from other commits;
	level 2 further categorizes merges by strategy
	"""

	_FEATURE_FINISH = auto()
	_VERSION_RELEASE = auto()
	_OTHER_MERGE = auto()

	# Public Member  -----------------------------------------------------------

	MERGE = auto()
	OTHER_COMMIT = auto()

	FEATURE_FINISH = MERGE | _FEATURE_FINISH
	VERSION_RELEASE = MERGE | _VERSION_RELEASE
	OTHER_MERGE = MERGE | _OTHER_MERGE
