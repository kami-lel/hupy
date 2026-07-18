"""
skip_once.py

define the ``skip-once`` accessor key's ``run_get``, ``run_set``,
``run_unset``, and ``run_info``
"""

# constants  ###################################################################
KEY = "skip-once"
DOC = "temporary skip module(s) for the current/next chain"

SKIPPABLE_MODULE = ("vg", "ttg", "pt", "pch", "bdc", "hb")

_MODULE_ABBR_TO_NAME = dict(
    zip(
        SKIPPABLE_MODULE,
        # ordered to line up with SKIPPABLE_MODULE
        (
            "ver-grep",
            "triage-tag-gating",
            "paper-trail",
            "prepend-commit-header",
            "ban-direct-commit",
            "hook-bracket",
        ),
    )
)

_MODULE_NAME_TO_ABBR = {
    name: abbr for abbr, name in _MODULE_ABBR_TO_NAME.items()
}


def _format_modules():
    return ",\n".join(
        "  {},\t{}".format(abbr, name)
        for abbr, name in _MODULE_ABBR_TO_NAME.items()
    )


# auxiliary  ###################################################################
def _resolve_abbrs(values):
    """
    translate each of ``values`` (abbr or full name) to its abbr,
    rejecting anything outside ``SKIPPABLE_MODULE``.
    """
    abbrs = []
    for value in values:
        abbr = _MODULE_NAME_TO_ABBR.get(value, value)
        if abbr not in SKIPPABLE_MODULE:
            raise SystemExit(
                "unknown module: {}\nMODULEs:\n{}".format(
                    value, _format_modules()
                )
            )
        abbrs.append(abbr)
    return abbrs


# Public API  ##################################################################
def run_get(repo, state_file, logger, args):
    """
    print the module(s) currently scheduled to be skipped once.
    """
    print(", ".join(sorted(state_file.skip_once)))


def run_set(repo, state_file, logger, args):
    """
    schedule module(s) to be skipped for the rest of the current (or
    next) chain; no VALUE resets to the default (empty).
    """
    if not args.value:
        state_file.skip_once.clear()
        logger.warning("reset to empty")
        return

    abbrs = _resolve_abbrs(args.value)
    state_file.skip_once.update(abbrs)
    logger.done("set one-time skip: {}".format(", ".join(abbrs)))


def run_unset(repo, state_file, logger, args):
    """
    unset previously scheduled one-time skip(s).
    """
    if not args.value:
        logger.error("no modules given")
        raise SystemExit(1)

    abbrs = _resolve_abbrs(args.value)
    state_file.skip_once.difference_update(abbrs)
    logger.done("unset one-time skip: {}".format(", ".join(abbrs)))


def run_info(repo, state_file, logger, args):
    """
    print extended info for the ``skip-once`` key.
    """
    print("""{}

each given module is skipped exactly once, for the rest of the
current chain (or the next one, if none is running); q.v.
docs/chain_doc.md for the chain concept

MODULEs:
{}

usage:
  $ hupy set skip-once MODULE [MODULE ...]
  $ hupy unset skip-once MODULE [MODULE ...]
  $ hupy get skip-once""".format(DOC, _format_modules()))
