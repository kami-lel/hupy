"""
perform_paper_trail.py

run the Paper Trail entries configured for a HUPy git hook: abort
the commit if an applicable paper trail's glob matches no file
changed in this commit
"""

import fnmatch
import sys

from hupy.kamilog import AnsiRenderer, AnsiStyle, getLogger
from hupy.cbm.get_current_commit_type import get_current_commit_type
from hupy.config_file.load_config import load_hupy_config
from hupy.should_run_module import should_run_module
from . import PT_LOGGER_NAME
from .changed_files import get_changed_file_paths

# logger  ######################################################################
logger = getLogger(PT_LOGGER_NAME)
logger.propagate = False


# constants  ###################################################################

_renderer = AnsiRenderer(sys.stdout)


# auxiliaries  #################################################################


def _is_trail_applicable(trail, commit_type):
    """
    :param trail: a single configured paper trail
    :type trail: _PaperTrail
    :param commit_type: type of the current commit/merge
    :type commit_type: CommitType
    :return: if ``trail`` should be checked for the current commit type
    :rtype: bool
    """
    if not trail.allow_commit_types:
        return True  # no filter configured, always applicable

    logger.debug("allow commit types: {}".format(trail.allow_commit_types))

    return bool(trail.allow_commit_types & commit_type)


def _check_trail(heading, trail, changed_paths):
    """
    :param heading: label for this paper trail, used in logs
    :type heading: str
    :param trail: a single configured paper trail
    :type trail: _PaperTrail
    :param changed_paths: file paths changed by this hook invocation
    :type changed_paths: list[str]
    """
    if any(fnmatch.fnmatch(path, trail.glob) for path in changed_paths):
        logger.pass_("PT satisfied: {}".format(heading))
        return

    logger.fail("PT unsatisfied, no changed file matches: {}".format(heading))
    raise SystemExit(1)


# Public API  ##################################################################
def perform_paper_trail(repo, state_file, hook_name):
    """
    run every paper trail configured for ``hook_name``, aborting the
    commit if an applicable paper trail's glob matches no file
    changed in this commit.


    :param repo: git repository object
    :type repo: git.Repo
    :param state_file: the open HUPy state file, as yielded by
            ``open_state_file``
    :type state_file: HupyStateFile
    :param hook_name: hook name, eg ``"pre-commit"``
    :type hook_name: str
    """
    if not should_run_module(repo, state_file, "pt"):
        return

    logger.enter("Paper Trail for: {}".format(hook_name))

    trails = load_hupy_config(repo).pt.trails

    if not trails:
        logger.skip("no Paper Trail entries configured")
        return

    changed_paths = get_changed_file_paths(repo)
    commit_type = get_current_commit_type(repo)

    for trail in trails:
        heading = trail.remark or _renderer.color(
            trail.glob, AnsiStyle.UNDERLINE
        )
        logger.enter("Paper Trail: " + heading)

        if not _is_trail_applicable(trail, commit_type):
            logger.skip("due to commit type filtered: {}".format(heading))
            continue

        _check_trail(heading, trail, changed_paths)
