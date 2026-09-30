"""
kamilog.py

Lightweight Python logging wrapper with custom log levels, structured output,
ANSI colored logging, verbosity control, comment banner utilities, and CLI.

Q.v. https://github.com/kami-lel/kamilog for Project Main Page
Q.v. https://github.com/kami-lel/kamilog/tree/main/docs for Documentation
"""

from argparse import (
    ArgumentParser,
    ArgumentTypeError,
    RawDescriptionHelpFormatter,
)
import logging
import os
import shlex
import subprocess
import sys
import time
from collections import deque, namedtuple
from enum import Flag, IntEnum, auto
from logging import FileHandler, Formatter, StreamHandler
from string import Formatter as _TemplateParser

__all__ = (
    "kamilog_cli_main",
    "getLogger",
    "KamiLogger",
    "add_verbose_arguments",
    "calc_verbosity",
    "calc_logging_level",
    "set_logging_level_by_namespace",
    "set_logging_level_by_verbosity",
    # ANSI style
    "AnsiStyle",
    "AnsiRenderer",
    # log levels
    "NOTSET",
    "DEBUG",
    "ENTER",
    "SKIP",
    "INFO",
    "PASS",
    "SUCC",
    "NOTE",
    "TIP",
    "DONE",
    "HINT",
    "IMPORTANT",
    "WARNING",
    "CAUTION",
    "ERROR",
    "FAIL",
    "CRITICAL",
    # datetime format constants
    "DATEFMT_TIME",
    "DATEFMT_TIME_MS",
    "DATEFMT_DATETIME",
    "DATEFMT_DATETIME_MS",
    # comment banner
    "gen_comment_banner_centered",
    "gen_comment_banner_left_just",
    "gen_comment_banner_right_just",
    "gen_comment_banner_zero",
)


# metadata  ####################################################################
__version__ = "2.10.0"
__author__ = "kamiLeL"


# enum  ########################################################################
class _CustomLogLevel(IntEnum):
    """
    custom log level IntEnum with padded 5-char display name


    :param value: numeric log level (used as the enum's int value)
    :type value: int
    :param display: padded 5-character display string for formatter output
    :type display: str
    """

    def __new__(cls, value, display):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.display = display
        return obj

    ENTER = (15, "ENTER")
    SKIP = (16, "SKIP ")
    SUCC = (17, "SUCC.")
    PASS = (21, "PASS ")
    NOTE = (23, "NOTE ")
    TIP = (24, "TIP  ")
    DONE = (25, "DONE ")
    HINT = (26, "HINT ")
    IMPORTANT = (27, "IMPT.")
    CAUTION = (31, "CAUT.")
    FAIL = (45, "FAIL ")


# level registration during import
for _lvl in _CustomLogLevel:
    logging.addLevelName(int(_lvl), _lvl.name)


# ANSI Color   #################################################################


class AnsiStyle(Flag):  # =====================================================
    """
    style/foreground/background flags, combinable via ``|``;
    values carry no ANSI meaning, q.v. ``AnsiRenderer._ANSI_STYLE2CODE``
    for the code lookup
    """

    # foreground color  --------------------------------------------------------

    RED = auto()
    BRIGHT_RED = auto()
    YELLOW = auto()
    BRIGHT_YELLOW = auto()
    GREEN = auto()
    BRIGHT_GREEN = auto()
    CYAN = auto()
    BRIGHT_CYAN = auto()
    BLUE = auto()
    BRIGHT_BLUE = auto()
    MAGENTA = auto()
    BRIGHT_MAGENTA = auto()

    BLACK = auto()
    GREY = auto()
    WHITE = auto()
    BRIGHT_WHITE = auto()

    # background color  --------------------------------------------------------

    BG_RED = auto()
    BG_BRIGHT_RED = auto()
    BG_YELLOW = auto()
    BG_BRIGHT_YELLOW = auto()
    BG_GREEN = auto()
    BG_BRIGHT_GREEN = auto()
    BG_CYAN = auto()
    BG_BRIGHT_CYAN = auto()
    BG_BLUE = auto()
    BG_BRIGHT_BLUE = auto()
    BG_MAGENTA = auto()
    BG_BRIGHT_MAGENTA = auto()

    BG_BLACK = auto()
    BG_GREY = auto()
    BG_WHITE = auto()
    BG_BRIGHT_WHITE = auto()

    # style  -------------------------------------------------------------------

    BOLD = auto()
    UNDERLINE = auto()

    # Public API  **************************************************************

    @classmethod
    def parse(cls, raw):
        """
        parse a comma-separated list of ``AnsiStyle`` member names into a
        single combined ``AnsiStyle`` value


        :param raw: comma-separated member names, eg ``"RED,BOLD"``
        :type raw: str
        :raises ValueError: ``raw`` contains an unknown member name
        :return: combined style
        :rtype: AnsiStyle
        """
        style = cls(0)
        for name in raw.split(","):
            name = name.strip().upper()
            try:
                style |= cls[name]
            except KeyError:
                raise ValueError("unknown AnsiStyle member {!r}".format(name))
        return style


class AnsiRenderer:  # =========================================================
    """
    TTY-aware ANSI color code renderer, detects TTY status at construction


    :param stream: output stream used for TTY detection;
            ``None`` disables color unconditionally
    :type stream: IO or None
    :param is_disabled: whether to disable color unconditionally,
            regardless of ``stream``; default=False
    :type is_disabled: bool, optional
    """

    _RESET = "\033[0m"

    _ANSI_STYLE2CODE = {
        AnsiStyle.BOLD: "1",
        AnsiStyle.UNDERLINE: "4",
        AnsiStyle.RED: "31",
        AnsiStyle.BRIGHT_RED: "91",
        AnsiStyle.YELLOW: "33",
        AnsiStyle.BRIGHT_YELLOW: "93",
        AnsiStyle.GREEN: "32",
        AnsiStyle.BRIGHT_GREEN: "92",
        AnsiStyle.CYAN: "36",
        AnsiStyle.BRIGHT_CYAN: "96",
        AnsiStyle.BLUE: "34",
        AnsiStyle.BRIGHT_BLUE: "94",
        AnsiStyle.MAGENTA: "35",
        AnsiStyle.BRIGHT_MAGENTA: "95",
        AnsiStyle.BLACK: "30",
        AnsiStyle.GREY: "90",
        AnsiStyle.WHITE: "37",
        AnsiStyle.BRIGHT_WHITE: "97",
        AnsiStyle.BG_RED: "41",
        AnsiStyle.BG_BRIGHT_RED: "101",
        AnsiStyle.BG_YELLOW: "43",
        AnsiStyle.BG_BRIGHT_YELLOW: "103",
        AnsiStyle.BG_GREEN: "42",
        AnsiStyle.BG_BRIGHT_GREEN: "102",
        AnsiStyle.BG_CYAN: "46",
        AnsiStyle.BG_BRIGHT_CYAN: "106",
        AnsiStyle.BG_BLUE: "44",
        AnsiStyle.BG_BRIGHT_BLUE: "104",
        AnsiStyle.BG_MAGENTA: "45",
        AnsiStyle.BG_BRIGHT_MAGENTA: "105",
        AnsiStyle.BG_BLACK: "40",
        AnsiStyle.BG_GREY: "100",
        AnsiStyle.BG_WHITE: "47",
        AnsiStyle.BG_BRIGHT_WHITE: "107",
    }

    _LEVEL2ANSI_COLOR = {
        logging.DEBUG: AnsiStyle.CYAN,
        _CustomLogLevel.ENTER: AnsiStyle.BRIGHT_CYAN,
        _CustomLogLevel.SKIP: AnsiStyle.BLUE,
        _CustomLogLevel.SUCC: AnsiStyle.GREEN,
        logging.INFO: AnsiStyle.BRIGHT_BLUE,
        _CustomLogLevel.PASS: AnsiStyle.BRIGHT_GREEN,
        _CustomLogLevel.NOTE: AnsiStyle.BLUE,
        _CustomLogLevel.TIP: AnsiStyle.BRIGHT_CYAN,
        _CustomLogLevel.DONE: AnsiStyle.BRIGHT_YELLOW,
        _CustomLogLevel.HINT: AnsiStyle.CYAN,
        _CustomLogLevel.IMPORTANT: AnsiStyle.BRIGHT_BLUE,
        logging.WARNING: AnsiStyle.YELLOW,
        _CustomLogLevel.CAUTION: AnsiStyle.MAGENTA,
        logging.ERROR: AnsiStyle.RED,
        _CustomLogLevel.FAIL: AnsiStyle.BRIGHT_RED,
        logging.CRITICAL: AnsiStyle.BRIGHT_MAGENTA,
    }

    _TRIAGE_TAG2ANSI_STYLE = {
        "BUG": AnsiStyle.BRIGHT_WHITE | AnsiStyle.BG_MAGENTA | AnsiStyle.BOLD,
        "Bug": AnsiStyle.BLACK | AnsiStyle.BG_BRIGHT_MAGENTA,
        "bug": AnsiStyle.MAGENTA,
        "FIXME": AnsiStyle.BRIGHT_WHITE | AnsiStyle.BG_BLUE | AnsiStyle.BOLD,
        "Fixme": AnsiStyle.BLACK | AnsiStyle.BG_BRIGHT_BLUE,
        "fixme": AnsiStyle.BLUE,
        "HACK": AnsiStyle.BLACK | AnsiStyle.BG_CYAN | AnsiStyle.BOLD,
        "Hack": AnsiStyle.BLACK | AnsiStyle.BG_BRIGHT_CYAN,
        "hack": AnsiStyle.CYAN,
        "TODO": AnsiStyle.BLACK | AnsiStyle.BG_YELLOW | AnsiStyle.BOLD,
        "Todo": AnsiStyle.BLACK | AnsiStyle.BG_BRIGHT_YELLOW,
        "todo": AnsiStyle.YELLOW,
    }

    def __init__(self, stream=None, *, is_disabled=False):
        self._enabled = (
            not is_disabled
            and stream is not None
            and hasattr(stream, "isatty")
            and stream.isatty()
        )

    # Public API  **************************************************************

    def color(self, text, style):
        """
        apply ANSI style codes to text


        :param text: text to colorize
        :type text: str
        :param style: ANSI style to apply, combine flags with ``|``,
                eg ``AnsiStyle.BOLD | AnsiStyle.RED | AnsiStyle.BG_YELLOW``
        :type style: AnsiStyle
        :return: ``text`` with style applied if color is enabled;
                otherwise ``text`` unchanged
        :rtype: str
        """
        if not self._enabled:
            return text

        codes = [
            code
            for flag, code in self._ANSI_STYLE2CODE.items()
            if flag in style
        ]
        return "\033[{}m{}{}".format(";".join(codes), text, self._RESET)

    def color_grey(self, text):
        """
        apply bright-black (grey) ANSI color to ``text``


        :param text: text to colorize
        :type text: str
        :return: ``text`` in grey if color is enabled; otherwise unchanged
        :rtype: str
        """
        return self.color(text, AnsiStyle.GREY)

    def color_level(self, text, levelno):
        """
        apply bold and level-specific ANSI color to ``text``


        :param text: text to colorize
        :type text: str
        :param levelno: numeric log level used to select the color
        :type levelno: int
        :return: ``text`` with the level's style applied if color is enabled
                and the level is known; otherwise ``text`` unchanged
        :rtype: str
        """
        color = self._LEVEL2ANSI_COLOR.get(levelno)
        if color is None:
            return text
        return self.color(text, color | AnsiStyle.BOLD)

    def color_badge(self, text, badge):
        """
        apply the badge's hue to ``text``; custom badges get magenta


        :param text: badge label text to colorize
        :type text: str
        :param badge: badge whose hue is used, eg ``"dry"``
        :type badge: str
        :return: ``text`` with style applied if color is enabled;
                otherwise ``text`` unchanged
        :rtype: str
        """
        hue = _NATIVE_BADGES.get(badge, (AnsiStyle.MAGENTA, 0))[0]
        return self.color(text, hue)

    def color_triage_tag(self, triage_tag):
        """
        apply tag-specific ANSI color to ``triage_tag``


        :param triage_tag: triage tag text,
                eg ``"BUG"``, ``"Fixme"``, ``"todo"``
        :type triage_tag: str
        :raises ValueError: ``triage_tag`` is not a recognized triage tag
        :return: ``triage_tag`` with style applied
        :rtype: str
        """
        style = self._TRIAGE_TAG2ANSI_STYLE.get(triage_tag)
        if style is None:
            raise ValueError(
                "param triage_tag {!r} is not a recognized triage tag".format(
                    triage_tag
                )
            )
        return self.color(triage_tag, style)


# Custom Logging  ##############################################################

# constants  ===================================================================

NOTSET = logging.NOTSET  # 0
DEBUG = logging.DEBUG  # 10
ENTER = _CustomLogLevel.ENTER  # 15
SKIP = _CustomLogLevel.SKIP  # 16
SUCC = _CustomLogLevel.SUCC  # 17
INFO = logging.INFO  # 20
PASS = _CustomLogLevel.PASS  # 21
NOTE = _CustomLogLevel.NOTE  # 23
TIP = _CustomLogLevel.TIP  # 24
DONE = _CustomLogLevel.DONE  # 25
HINT = _CustomLogLevel.HINT  # 26
IMPORTANT = _CustomLogLevel.IMPORTANT  # 27
WARNING = logging.WARNING  # 30
CAUTION = _CustomLogLevel.CAUTION  # 31
ERROR = logging.ERROR  # 40
FAIL = _CustomLogLevel.FAIL  # 45
CRITICAL = logging.CRITICAL  # 50


# Datetime Formats  ============================================================
DATEFMT_TIME = "%H:%M:%S"
DATEFMT_TIME_MS = "%H:%M:%S.{ms}"
DATEFMT_DATETIME = "%Y-%m-%d %H:%M:%S"
DATEFMT_DATETIME_MS = "%Y-%m-%d %H:%M:%S.{ms}"

# marks datefmt as unset, so each destination picks its own dft
_DATEFMT_AUTO = object()


# Badges  ======================================================================
# native badge label → (hue, priority); higher priority prints earlier
_NATIVE_BADGES = {
    "dry": (AnsiStyle.BRIGHT_YELLOW, 45),
    "chk": (AnsiStyle.YELLOW, 44),
    "mock": (AnsiStyle.YELLOW, 43),
    "sbx": (AnsiStyle.GREEN, 33),
    "force": (AnsiStyle.RED, 52),
    "undo": (AnsiStyle.RED, 51),
    "unsafe": (AnsiStyle.BRIGHT_RED, 53),
    "yes": (AnsiStyle.YELLOW, 42),
    "auto": (AnsiStyle.BLUE, 13),
    "strict": (AnsiStyle.GREEN, 32),
    "keep": (AnsiStyle.YELLOW, 41),
    "fast": (AnsiStyle.GREEN, 31),
    "retries": (AnsiStyle.CYAN, 25),
    "resm": (AnsiStyle.CYAN, 24),
    "new": (AnsiStyle.CYAN, 23),
    "offl": (AnsiStyle.CYAN, 22),
    "incr": (AnsiStyle.CYAN, 21),
    "watch": (AnsiStyle.BLUE, 12),
    "bg": (AnsiStyle.BLUE, 11),
}


def _normalize_badges(badges):
    """
    drop duplicate badges, then order by descending priority;
    customs rank 0 and keep the order given
    """
    if badges is None:
        return ()
    if isinstance(badges, str):
        badges = (badges,)
    unique = tuple(dict.fromkeys(badges))
    return tuple(
        sorted(unique, key=lambda b: -_NATIVE_BADGES.get(b, (None, 0))[1])
    )


# Deeds  =======================================================================
_Deed = namedtuple(
    "_Deed", ("name", "arg_names", "template", "level", "err_level")
)


# deed → fixed wording & severities; see docs/deed-doc.md
_DEEDS = {
    d.name: d
    for d in (
        _Deed("create_file", ("path",), "create {path}", INFO, ERROR),
        _Deed("owr_file", ("path",), "overwrite {path}", WARNING, ERROR),
        _Deed("append_file", ("path",), "append {path}", INFO, ERROR),
        _Deed(
            "cp_file",
            ("source", "destination"),
            "copy {source} -> {destination}",
            INFO,
            ERROR,
        ),
        _Deed(
            "mv_file",
            ("source", "destination"),
            "move {source} -> {destination}",
            INFO,
            ERROR,
        ),
        _Deed(
            "chmod_file",
            ("path", "mode"),
            "chmod {path} {mode}",
            INFO,
            ERROR,
        ),
        _Deed("rm_file", ("path",), "delete {path}", WARNING, WARNING),
        _Deed("create_dir", ("path",), "create dir {path}", INFO, ERROR),
        _Deed("rm_dir", ("path",), "delete dir {path}", WARNING, WARNING),
        _Deed(
            "pack_files",
            ("source", "archive"),
            "pack {source} -> {archive}",
            INFO,
            ERROR,
        ),
        _Deed(
            "unpack_archive",
            ("archive", "destination"),
            "unpack {archive} -> {destination}",
            INFO,
            ERROR,
        ),
        _Deed(
            "download",
            ("url", "destination"),
            "download {url} -> {destination}",
            INFO,
            ERROR,
        ),
        _Deed(
            "upload",
            ("source", "url"),
            "upload {source} -> {url}",
            INFO,
            ERROR,
        ),
        _Deed("run_command", ("command",), "run {command}", INFO, ERROR),
        _Deed("load_config", ("path",), "load {path}", INFO, ERROR),
        _Deed("save_config", ("path",), "save {path}", INFO, ERROR),
        _Deed("skip_file", ("path",), "skip {path}", SKIP, WARNING),
    )
}


def _stringify_deed_args(args):
    """
    str() each arg once when given, so a later change to the object can not
    alter the line; None stays None and still drops its segment
    """
    return tuple(None if arg is None else str(arg) for arg in args)


def _raise_unexpected_deed_arg(deed, key):
    """
    raise ``TypeError`` for argument ``key`` that ``deed`` does not accept
    """
    raise TypeError(
        "{}() got an unexpected argument '{}'".format(deed.name, key)
    )


def _bind_deed_methods(cls, make_method, qualname_prefix):
    """
    attach one method per deed to ``cls``, built by ``make_method``
    """
    for deed in _DEEDS.values():
        method = make_method(deed)
        method.__name__ = deed.name
        method.__qualname__ = "{}.{}".format(qualname_prefix, deed.name)
        setattr(cls, deed.name, method)


def _render_deed_message(deed, *args, **kwargs):
    """
    render `deed` wording from positional `args` and named `kwargs`;
    an omitted argument drops its segment, e.g. ` -> {destination}`
    """
    if len(args) > len(deed.arg_names):
        raise TypeError(
            "{}() takes at most {} arguments ({} given)".format(
                deed.name, len(deed.arg_names), len(args)
            )
        )
    values = dict(zip(deed.arg_names, args))
    for key, val in kwargs.items():
        if key not in deed.arg_names or key in values:
            _raise_unexpected_deed_arg(deed, key)
        values[key] = val

    # each field carries the literal before it; the 1st literal is the verb
    parts = []
    fields = _TemplateParser().parse(deed.template)
    for i, (literal, field, _, _) in enumerate(fields):
        is_given = values.get(field) is not None
        if i == 0:
            parts.append(literal if is_given else literal.rstrip())
        if is_given:
            if i > 0:
                parts.append(literal)
            parts.append(str(values[field]))
    return "".join(parts).rstrip()


class _DeedHandle:  # **********************************************************
    """
    handle yielded by a tracked deed block, ``with ... as act``;
    exposes :meth:`set` and :meth:`fail` only
    """

    def __init__(self, scope):
        self._scope = scope

    def set(self, **kwargs):
        """
        give arguments known only after the deed started; an argument still
        missing at block exit drops its segment, and a name the deed lacks or
        already got positionally raises ``TypeError``
        """
        self._scope.set_late_args(kwargs)

    def fail(self, detail):
        """
        mark the deed failed without raising, e.g. a bad exit status;
        the failure line reads ``fail to <message>: <detail>``
        and carries no traceback
        """
        self._scope.mark_failed(detail)


class _DeedScope:  # ***********************************************************
    """
    context manager of one tracked deed;
    logs one line at block exit: success, or failure if the block raised
    or the handle marked it failed
    """

    def __init__(self, logger, deed, args, options):
        self._logger = logger
        self._deed = deed
        self._args = args
        self._options = options
        self._late_args = {}
        self._fail_detail = None
        self._is_failed = False

    def __enter__(self):
        return _DeedHandle(self)

    def __exit__(self, exc_type, exc_value, traceback):
        # only Exception counts; KeyboardInterrupt & SystemExit pass silently
        if exc_type is not None:
            if not issubclass(exc_type, Exception):
                return False
            cause = exc_type.__name__
            if str(exc_value):
                cause = "{}: {}".format(cause, exc_value)
            self._log_failure(cause, (exc_type, exc_value, traceback))
            return self._options["suppress"]
        if self._is_failed:
            self._log_failure(self._fail_detail)
        else:
            self._log_success()
        return False

    def set_late_args(self, kwargs):
        """
        record arguments given after entry, validating each name
        """
        for key in kwargs:
            if key not in self._deed.arg_names:
                _raise_unexpected_deed_arg(self._deed, key)
            if self._deed.arg_names.index(key) < len(self._args):
                raise TypeError(
                    "{}() got multiple values for argument '{}'".format(
                        self._deed.name, key
                    )
                )
        values = _stringify_deed_args(kwargs.values())
        self._late_args.update(zip(kwargs, values))

    def mark_failed(self, detail):
        """
        mark the deed failed as a value; no exception involved
        """
        self._is_failed = True
        self._fail_detail = detail

    def _render(self):
        """
        render the deed wording from entry and late arguments
        """
        return _render_deed_message(self._deed, *self._args, **self._late_args)

    def _log_success(self):
        """
        log the success line at the deed's level
        """
        level = self._options["level"]
        level = self._deed.level if level is None else level
        self._emit(level, self._render())

    def _log_failure(self, cause, exc_info=None):
        """
        log `fail to <message>: <cause>`, with traceback if `exc_info`
        """
        err_level = self._options["err_level"]
        err_level = self._deed.err_level if err_level is None else err_level
        message = "fail to {}".format(self._render())
        if cause is not None and str(cause):
            message = "{}: {}".format(message, cause)
        self._emit(err_level, message, exc_info)

    def _emit(self, level, message, exc_info=None):
        """
        log `message`, attributed to the code holding the `with`
        """
        self._logger._log_if_enabled(
            level,
            message,
            (),
            4,
            exc_info=exc_info,
            badges=self._options["badges"],
            is_inheriting_badges=self._options["is_inheriting_badges"],
        )


class _DeedTrack:  # ***********************************************************
    """
    namespace behind ``logger.track``;
    holds one method per deed, each returning a :class:`_DeedScope`
    """

    def __init__(self, logger):
        self._logger = logger


def _make_track_method(deed):
    """
    build the track-form method of `deed` for :class:`_DeedTrack`
    """

    def track_method(
        self,
        *args,
        level=None,
        err_level=None,
        suppress=False,
        badges=None,
        is_inheriting_badges=True
    ):
        args = _stringify_deed_args(args)
        # render once so a bad arg raises at the call, not at block exit
        _render_deed_message(deed, *args)
        options = {
            "level": level,
            "err_level": err_level,
            "suppress": suppress,
            "badges": badges,
            "is_inheriting_badges": is_inheriting_badges,
        }
        return _DeedScope(self._logger, deed, args, options)

    track_method.__doc__ = """
        track the deed ``{template}``: one line is logged when the block
        exits, at ``level`` on success or at ``err_level`` on an
        ``Exception``, which then propagates unless ``suppress``; the block
        yields a handle with ``set(name=value)`` and ``fail(detail)``


        :param args: the deed's own arguments, in order ``{arg_names}``
        :type args: object
        :param level: severity of the success line; default=the deed's level
        :type level: int, optional
        :param err_level: severity of the failure line;
                default=the deed's error level
        :type err_level: int, optional
        :param suppress: whether to swallow the exception after logging it;
                default=False
        :type suppress: bool, optional
        :param badges: badge labels for this record only; default=None
        :type badges: str or Iterable(str), optional
        :param is_inheriting_badges: whether the run-wide badges apply to
                this record; default=True
        :type is_inheriting_badges: bool, optional
        :return: context manager logging the outcome at block exit
        """.format(
        template=deed.template, arg_names=", ".join(deed.arg_names)
    )
    return track_method


_bind_deed_methods(_DeedTrack, _make_track_method, "_DeedTrack")


class KamiLogger(logging.Logger):  # ===========================================
    """
    logger subclass extending :class:`logging.Logger` with custom levels

    provides convenience methods for test and hook workflows;
    obtain instances via :func:`getlogger`
    """

    # run-wide badges; instances shadow this on first set_badges call
    _run_badges = ()

    def enter(self, message, *args, **kwargs):
        """
        log at ``ENTER`` level (15): entering a hook or test case


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(ENTER, message, args, 2, **kwargs)

    def skip(self, message, *args, **kwargs):
        """
        log at ``SKIP`` level (16): skipping a hook or test case


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(SKIP, message, args, 2, **kwargs)

    def succ(self, message, *args, **kwargs):
        """
        log at ``SUCC`` level (17): task or operation succeeded


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(SUCC, message, args, 2, **kwargs)

    def pass_(self, message, *args, **kwargs):
        """
        log at ``PASS`` level (21): hook or test case passed


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(PASS, message, args, 2, **kwargs)

    def note(self, message, *args, **kwargs):
        """
        log at ``NOTE`` level (23): general aside worth noting


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(NOTE, message, args, 2, **kwargs)

    def tip(self, message, *args, **kwargs):
        """
        log at ``TIP`` level (24): actionable suggestion


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(TIP, message, args, 2, **kwargs)

    def done(self, message, *args, **kwargs):
        """
        log at ``DONE`` level (25): task or operation completed


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(DONE, message, args, 2, **kwargs)

    def hint(self, message, *args, **kwargs):
        """
        log at ``HINT`` level (26): subtle, barely-there cue


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(HINT, message, args, 2, **kwargs)

    def important(self, message, *args, **kwargs):
        """
        log at ``IMPORTANT`` level (27): emphasized information


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(IMPORTANT, message, args, 2, **kwargs)

    def caution(self, message, *args, **kwargs):
        """
        log at ``CAUTION`` level (31): risk of a negative outcome


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(CAUTION, message, args, 2, **kwargs)

    def fail(self, message, *args, **kwargs):
        """
        log at ``FAIL`` level (45): hook or test case failed


        :param message: message, or ``%``-style format string for ``args``
        :type message: str
        :param args: values interpolated into ``message``
        :type args: object
        :param kwargs: forwarded to ``logging.Logger._log``: ``exc_info``,
                ``extra``, ``stack_info``, ``badges``, ``is_inheriting_badges``
        :type kwargs: object
        """
        self._log_if_enabled(FAIL, message, args, 2, **kwargs)

    @property
    def track(self):
        """
        track form of the deed methods, e.g. ``with logger.track.cp_file(a, b)``


        :return: namespace whose methods mirror the plain deed methods
        :rtype: _DeedTrack
        """
        return _DeedTrack(self)

    def set_badges(self, badges=None):
        """
        replace the run-wide badges

        an omitted, ``None`` or empty ``badges`` unsets every run-wide
        badge; there is no add or remove of a single badge


        :param badges: badge labels for every later record;
                default=None
        :type badges: str or Iterable(str), optional
        """
        self._run_badges = _normalize_badges(badges)

    def clear_badges(self):
        """
        unset every run-wide badge
        """
        self._run_badges = ()

    def _log_if_enabled(self, level, msg, args, stacklevel, **kwargs):
        """
        log at ``level`` if enabled; ``stacklevel`` counts from the
                method calling this helper, as if it called ``_log``
        """
        if self.isEnabledFor(level):
            self._log(level, msg, args, stacklevel=stacklevel + 1, **kwargs)

    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        badges=None,
        is_inheriting_badges=True,
    ):
        """
        stamp the record with its effective badges, then log as usual;
        per-call ``badges`` add to the run-wide set unless
        ``is_inheriting_badges`` is false, and the result lands on
        ``record.badges`` as a priority-sorted tuple
        """
        run_badges = self._run_badges if is_inheriting_badges else ()
        extra = dict(extra) if extra else {}
        extra["badges"] = _normalize_badges(
            (*run_badges, *_normalize_badges(badges))
        )
        # +1 skips this frame so caller info stays correct
        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
        )


def _make_deed_method(deed):
    """
    build the plain-form method of `deed` for :class:`KamiLogger`
    """

    def deed_method(
        self, *args, level=None, badges=None, is_inheriting_badges=True
    ):
        level = deed.level if level is None else level
        if self.isEnabledFor(level):
            self._log(
                level,
                _render_deed_message(deed, *args),
                (),
                stacklevel=2,
                badges=badges,
                is_inheriting_badges=is_inheriting_badges,
            )

    deed_method.__doc__ = """
        log the deed ``{template}`` at ``{level}`` level by default


        :param args: the deed's own arguments, in order ``{arg_names}``;
                trailing ones may be omitted
        :type args: object
        :param level: severity of the line; default=the deed's level
        :type level: int, optional
        :param badges: badge labels for this record only; default=None
        :type badges: str or Iterable(str), optional
        :param is_inheriting_badges: whether the run-wide badges apply to
                this record; default=True
        :type is_inheriting_badges: bool, optional
        """.format(
        template=deed.template,
        level=logging.getLevelName(deed.level),
        arg_names=", ".join(deed.arg_names),
    )
    return deed_method


_bind_deed_methods(KamiLogger, _make_deed_method, "KamiLogger")


logging.setLoggerClass(KamiLogger)
# root logger exists before setLoggerClass — patch its class directly
logging.root.__class__ = KamiLogger


# log formatting  # ============================================================


# stdlib levels padded to 5 chars; custom levels carry their own display
_PADDED_LEVELNAME_MAP = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO ",
    logging.WARNING: "WARN.",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRIT.",
    **{lvl: lvl.display for lvl in _CustomLogLevel},
}


class _LogFormatEngine:  # *****************************************************
    """
    core log-line formatting logic, independent of ``logging.Formatter``


    :param palette: color palette controlling ANSI output
    :type palette: _AnsiRenderer
    :param datefmt: strftime format string for wall-clock timestamps;
            ``None`` disables timestamps
    :type datefmt: str or None
    :param relative_to: Unix timestamp used as the epoch for relative
            time display
    :type relative_to: float or None
    """

    def __init__(self, palette, *, datefmt=None, relative_to=None):
        self._palette = palette
        self._datefmt = datefmt
        self._relative_to = relative_to

    # Public API  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def count_prefix_chars(self, record):
        """
        :return: printable character count before the message text of the
                record; with badges, the display column where that text starts
        :rtype: int
        """
        name = record.name
        has_name = self._has_source_name(name)

        if self._relative_to is not None:
            ts_len = len(self._fmt_relative(record.created))
        elif self._datefmt:
            ts_len = len(self._strftime_ms(self._datefmt, record))
        else:
            ts_len = 0

        level_len = 5  # always padded/truncated to 5
        space_len = 1 if has_name else 0
        source_len = len(name) + 1 if has_name else 1  # "name:" or ":"

        col = ts_len + 1 if ts_len else 0
        badges = getattr(record, "badges", ())
        if badges:
            # level starts on the first tab stop after the badges
            col += len(" ".join(badges))
            col += _calc_tab_advance(col)
        return col + level_len + space_len + source_len + 1

    def format_time(self, record, datefmt=None):
        """
        :return: timestamp of the record per ``datefmt`` or the engine's own
                format, colored; empty string when timestamps are disabled
        :rtype: str
        """
        if self._relative_to is not None:
            return self._fmt_asctime(self._fmt_relative(record.created))
        elif datefmt or self._datefmt:
            asctime = self._strftime_ms(datefmt or self._datefmt, record)
            return self._fmt_asctime(asctime)
        return ""

    def build_line(self, record):
        """
        :return: main log line of the record, without ``exc_info`` or
                ``stack_info``
        :rtype: str
        """
        asctime = self.format_time(record)
        source = self._fmt_source(record.name)
        space = " " if self._has_source_name(record.name) else ""
        badges = getattr(record, "badges", ())
        # badges sit b/t timestamp & level, level on the next tab stop
        badge_seg = "{}\t".format(self._fmt_badges(badges)) if badges else ""
        head = "{} ".format(asctime) if asctime else ""
        return "{}{}{}{}{} {}".format(
            head,
            badge_seg,
            self._fmt_level(record.levelno),
            space,
            source,
            record.getMessage(),
        )

    # helpers  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @staticmethod
    def _has_source_name(name):
        """
        :return: if ``name`` is a real logger name, not empty or root
        :rtype: bool
        """
        return bool(name and name != "root")

    @staticmethod
    def _strftime_ms(fmt, record):
        """
        :return: ``record`` creation time per ``fmt``, ``{ms}`` filled
                with zero-padded milliseconds
        :rtype: str
        """
        return time.strftime(fmt, time.localtime(record.created)).replace(
            "{ms}", "{:03d}".format(int(record.msecs))
        )

    def _fmt_asctime(self, asctime):
        """
        color ``asctime`` grey
        """
        return self._palette.color_grey(asctime)

    def _fmt_level(self, levelno):
        """
        build the padded, colored level-name segment
        """
        padded = _PADDED_LEVELNAME_MAP.get(levelno, str(levelno).ljust(5)[:5])
        return self._palette.color_level(padded, levelno)

    def _fmt_badges(self, badges):
        """
        build the space-separated, colored badge segment
        """
        return " ".join(self._palette.color_badge(b, b) for b in badges)

    def _fmt_source(self, name):
        """
        build the colored source-label segment
        """
        if not self._has_source_name(name):
            return self._palette.color_grey(":")
        return "{}{}".format(
            self._palette.color_grey(name),
            self._palette.color_grey(":"),
        )

    def _fmt_relative(self, created):
        """
        format elapsed time relative to ``_relative_to``
        """
        delta = created - self._relative_to
        sign = "-" if delta < 0 else "+"
        delta = abs(delta)
        h, rem = divmod(int(delta), 3600)
        m, s = divmod(rem, 60)
        ms = int((delta % 1) * 1000)
        return "{}{:02d}:{:02d}:{:02d}.{:03d}".format(sign, h, m, s, ms)


class _LogFormatter(Formatter):  # *********************************************
    """
    ``logging.Formatter`` adapter wrapping ``_LogFormatEngine``


    :param stream: forwarded to ``_AnsiRenderer`` for TTY detection;
            ``None`` disables color
    :type stream: IO or None
    :param datefmt: forwarded to ``_LogFormatEngine``; also passed to
            ``Formatter.__init__`` for stdlib compatibility
    :type datefmt: str or None
    :param relative_to: forwarded to ``_LogFormatEngine``
    :type relative_to: float or None
    :param disable_color: disable color regardless of ``stream``
    :type disable_color: bool
    """

    def __init__(
        self,
        stream=None,
        *,
        datefmt=None,
        relative_to=None,
        disable_color=False,
    ):
        super().__init__(datefmt=datefmt)
        self.palette = AnsiRenderer(stream, is_disabled=disable_color)
        self.engine = _LogFormatEngine(
            self.palette, datefmt=datefmt, relative_to=relative_to
        )

    def formatTime(self, record, datefmt=None):
        """
        :return: timestamp from the engine, honoring the ``datefmt`` override
        :rtype: str
        """
        return self.engine.format_time(record, datefmt)

    def format(self, record):
        """
        :return: complete log line, with ``exc_info`` and ``stack_info``
                appended when present
        :rtype: str
        """
        record = logging.makeLogRecord(record.__dict__)
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        result = self.engine.build_line(record)
        if record.exc_text:
            result = "{}\n{}".format(result, record.exc_text)
        if record.stack_info:
            result = "{}\n{}".format(
                result, self.formatStack(record.stack_info)
            )
        return result


# diff only message   ==========================================================


def _calc_tab_advance(col):
    """
    :return: columns from ``col`` to the next tab stop, a full
            ``TAB_SIZE`` when ``col`` already sits on one
    :rtype: int
    """
    return _TabAlignedLine.TAB_SIZE - col % _TabAlignedLine.TAB_SIZE


def _expand_tabs(line, start_offset):
    """
    :return: ``line`` with each tab replaced by spaces up to the next
            tab stop, ``line`` beginning at column ``start_offset``
    :rtype: str
    """
    expanded = []
    col = start_offset
    for ch in line:
        if ch == "\t":
            n_spaces = _calc_tab_advance(col)
            expanded.append(" " * n_spaces)
            col += n_spaces
        else:
            expanded.append(ch)
            col += 1
    return "".join(expanded)


class _TabAlignedLine(list):  # ************************************************
    """
    a line of text split into tab-stop-aligned string blocks
    """

    TAB_SIZE = 8

    @classmethod
    def parse(cls, line, *, start_offset=0):  # ++++++++++++++++++++++++++++++++
        """
        split a regular text line into ``TAB_SIZE``-wide blocks; the first is
        shortened by ``start_offset`` so later ones land on ``TAB_SIZE`` column
        boundaries, the last holds the remainder, and literal tabs in ``line``
        are expanded first
        """
        line = _expand_tabs(line, start_offset)

        # split blocks  --------------------------------------------------------
        n = len(line)
        blocks = []

        first_len = min(_calc_tab_advance(start_offset), n)
        pos = first_len
        blocks.append(line[:pos])

        while pos < n:
            end = min(pos + cls.TAB_SIZE, n)
            blocks.append(line[pos:end])
            pos = end

        return cls(blocks, start_offset=start_offset)

    def __init__(self, blocks, *, start_offset=0):
        super().__init__(blocks)
        self.start_offset = start_offset

    def render(self, *, insert_prefix=False, prefix_symbol=" "):
        """
        :return: the blocks joined into one line, ``start_offset`` copies of
                ``prefix_symbol`` prepended when ``insert_prefix``
        :rtype: str
        """
        line = "".join(self)
        if insert_prefix:
            return prefix_symbol * self.start_offset + line
        return line

    def __str__(self):
        return self.render()


class _DiffOnlyEngine:  # ******************************************************
    """
    engine for diff-only compression of log message text


    :param formatter: formatter used to measure the prefix width and
            apply ``color_grey`` to compression markers
    :type formatter: _LogFormatter
    :param threshold: number of prior messages held for comparison
    :type threshold: int
    """

    _FALLBACK_TAB_SPAN = 2
    _COMPRESSION_MARKER = "〃\t"  # visual width matches one TAB_SIZE block
    _MARKER_CHAR = "〃"
    _MARKER_WIDTH = 2  # rendered columns of _MARKER_CHAR
    _LEADER_MARKER_MIN = 4  # leader shorter than this becomes bare "\t"
    _LONG_LINE_COLS = 100  # wider rendered lines drop tab alignment
    _LONG_LINE_MARKER = "〃 "  # full-block ditto on a long line

    def __init__(self, formatter, threshold=3):
        self._formatter = formatter
        # each entry: one message split into its lines
        self._history = deque(maxlen=threshold)
        # _common[k][i] = shared char at position i of line k across all
        # history, or None where messages diverge or lengths differ; a
        # line missing from any history message has an empty list
        self._common = []

    def _update_common(self):
        """
        recompute ``_common`` from the current ``_history`` messages
        """
        history = list(self._history)
        if not history:
            self._common = []
            return
        n_lines = max(len(lines) for lines in history)
        self._common = [
            (
                self._calc_line_common([lines[k] for lines in history])
                if all(k < len(lines) for lines in history)
                else []
            )
            for k in range(n_lines)
        ]

    @staticmethod
    def _calc_line_common(texts):
        """
        :return: per-position shared char across ``texts``, ``None``
                where they diverge or lengths differ
        :rtype: list[str or None]
        """
        min_len = min(len(s) for s in texts)
        max_len = max(len(s) for s in texts)
        common = []
        for i in range(max_len):
            if i >= min_len:
                common.append(None)  # position missing in some texts
            else:
                ch = texts[0][i]
                common.append(
                    ch if all(s[i] == ch for s in texts[1:]) else None
                )
        return common

    @staticmethod
    def _is_word_char(ch):
        """
        :return: if ``ch`` is a word character (``0-9A-Za-z`` or ``-_``)
        :rtype: bool
        """
        return (ch.isascii() and ch.isalnum()) or ch in "-_"

    def _find_cut(self, message, run_s, run_e, prefix_len):
        """
        :return: cut index in ``[run_s, run_e]``, text before it replaceable
                and text from it kept printed; lands on the nearest non-word
                char scanning back from the run end, at most
                ``_FALLBACK_TAB_SPAN`` tab stops, else on that tab-aligned floor
        :rtype: int
        """
        block = _TabAlignedLine.TAB_SIZE
        col_e = prefix_len + run_e
        floor_col = (col_e // block - self._FALLBACK_TAB_SPAN) * block
        cut_min = max(run_s, floor_col - prefix_len)
        for b in range(run_e - 1, cut_min - 1, -1):
            if not self._is_word_char(message[b]):
                return b
        return cut_min

    def _compress(self, record, message):
        """
        compress ``message`` line by line against the matching history lines;
        only line 1 carries the record prefix, later lines start at column 0
        """
        prefix_len = self._formatter.engine.count_prefix_chars(record)
        lines = message.split("\n")
        return "\n".join(
            self._compress_line(
                line,
                self._common[k] if k < len(self._common) else [],
                prefix_len if k == 0 else 0,
            )
            for k, line in enumerate(lines)
        )

    @classmethod
    def _is_long_line(cls, line, prefix_len):
        """
        :return: if the rendered, uncompressed ``line`` starting at
                column ``prefix_len`` ends beyond ``_LONG_LINE_COLS``,
                embedded tabs expanded to tab stops
        :rtype: bool
        """
        return prefix_len + len(_expand_tabs(line, prefix_len)) > (
            cls._LONG_LINE_COLS
        )

    def _compress_line(self, message, common, prefix_len):
        """
        compress positions of one line matching ``common`` into ``〃\\t``
        markers; the replaceable span (``run_s`` to ``cut``) is split into
        ``_TabAlignedLine`` blocks anchored at its absolute column, so a short
        leading block (if any) is the leader, a short trailing block (if any)
        is the gap, and everything between is a whole replaceable tab stop
        """
        n_common = len(common)
        is_common = [
            i < n_common and common[i] is not None and common[i] == ch
            for i, ch in enumerate(message)
        ]
        is_long = self._is_long_line(message, prefix_len)
        result = []
        i = 0
        msg_len = len(message)
        while i < msg_len:
            if not is_common[i]:
                result.append(message[i])
                i += 1
            else:
                run_s = i
                while i < msg_len and is_common[i]:
                    i += 1
                result.append(
                    self._render_run(message, run_s, i, prefix_len, is_long)
                )
        return "".join(result)

    def _render_run(self, message, run_s, run_e, prefix_len, is_long):
        """
        render one common run as markers plus its kept tail;
        ``is_long`` flags a line wider than ``_LONG_LINE_COLS``
        """
        block = _TabAlignedLine.TAB_SIZE
        grey = self._formatter.palette.color_grey
        cut = self._find_cut(message, run_s, run_e, prefix_len)

        tal_blocks = list(
            _TabAlignedLine.parse(
                message[run_s:cut], start_offset=prefix_len + run_s
            )
        )
        leader = ""
        if tal_blocks and len(tal_blocks[0]) < block:
            leader = tal_blocks.pop(0)
        if tal_blocks and len(tal_blocks[-1]) < block:
            gap_block = tal_blocks.pop()
        else:
            gap_block = ""
        k = len(tal_blocks)  # remaining blocks are all full-width

        if k == 0:
            return message[run_s:run_e]
        result = []
        gap = len(gap_block)
        block_marker = (
            self._LONG_LINE_MARKER if is_long else self._COMPRESSION_MARKER
        )
        # leader: common chars before the first tab stop are never
        # printed; short ones become a bare tab jump, longer ones earn
        # their own marker; a long line has no tab stops to jump to
        if len(leader) >= self._LEADER_MARKER_MIN:
            result.append(grey(block_marker))
        elif leader and not is_long:
            result.append("\t")
        result.append(grey(block_marker * k))
        # partial block: marker + spaces padding to the cut; a long line
        # keeps the marker and its one space, no padding
        if gap >= self._MARKER_WIDTH:
            if is_long:
                result.append(grey(block_marker))
            else:
                result.append(grey(self._MARKER_CHAR))
                result.append(" " * (gap - self._MARKER_WIDTH))
        elif not is_long:
            result.append(" " * gap)
        result.append(message[cut:run_e])
        return "".join(result)

    def process(self, record):
        """
        :return: message of the record compressed against history; unchanged
                during warmup
        :rtype: str
        """
        message = record.getMessage()

        if len(self._history) == self._history.maxlen:
            masked = self._compress(record, message)
        else:
            masked = message

        self._history.append(message.split("\n"))
        self._update_common()
        return masked


class _DiffOnlyMsgFilter(logging.Filter):  # ***********************************
    """
    ``logging.Filter`` adapter that applies ``_DiffOnlyEngine`` to records


    :param formatter: forwarded to ``_DiffOnlyEngine`` for prefix-width
            measurement; pass ``None`` to disable prefix alignment
    :type formatter: _LogFormatter or None
    :param threshold: forwarded to ``_DiffOnlyEngine`` as the history
            depth before compression activates
    :type threshold: int
    :param disable_diff_only_compression: whether turn off diff-ony compression
            and pass records through untouched
    :type disable_diff_only_compression: bool
    """

    def __init__(
        self, formatter, threshold=3, *, disable_diff_only_compression=False
    ):
        super().__init__()
        self._engine = (
            None
            if disable_diff_only_compression
            else _DiffOnlyEngine(formatter, threshold)
        )

    def filter(self, record):
        """
        :return: always ``True``; the filter compresses ``record.msg`` in place
                and never drops records
        :rtype: bool
        """
        if self._engine is None:  # compression disabled, pass through
            return True
        record.msg = self._engine.process(record)
        record.args = ()
        return True


# Logger Public API  ===========================================================


def _attach_diff_only_filter(logger, formatter_kwargs, is_disabled):
    """
    attach a diff-only filter to ``logger`` unless it already has one
    """
    if any(isinstance(f, _DiffOnlyMsgFilter) for f in logger.filters):
        return
    logger.addFilter(
        _DiffOnlyMsgFilter(
            _LogFormatter(sys.stdout, **formatter_kwargs),
            disable_diff_only_compression=is_disabled,
        )
    )


def _build_console_handler(stream, formatter_kwargs, level_filter):
    """
    :return: handler on ``stream`` passing only records ``level_filter``
            accepts, formatted for that stream's TTY
    :rtype: logging.StreamHandler
    """
    handler = StreamHandler(stream)
    handler.setFormatter(_LogFormatter(stream, **formatter_kwargs))
    handler.addFilter(level_filter)
    return handler


def _attach_console_handlers(logger, formatter_kwargs):
    """
    attach stdout (below ``WARNING``) and stderr handlers to ``logger``
    unless it already has a console handler
    """
    if any(
        isinstance(h, StreamHandler) and not isinstance(h, FileHandler)
        for h in logger.handlers
    ):
        return
    logger.addHandler(
        _build_console_handler(
            sys.stdout, formatter_kwargs, lambda r: r.levelno < logging.WARNING
        )
    )
    logger.addHandler(
        _build_console_handler(
            sys.stderr,
            formatter_kwargs,
            lambda r: r.levelno >= logging.WARNING,
        )
    )


def _attach_file_handler(logger, filename, file_mode, formatter_kwargs):
    """
    attach a file handler for ``filename`` to ``logger`` unless one
    already targets that file
    """
    target = os.path.abspath(filename)  # same file under any spelling
    if any(
        isinstance(h, FileHandler) and h.baseFilename == target
        for h in logger.handlers
    ):
        return
    file_handler = FileHandler(filename, mode=file_mode, encoding="utf-8")
    file_handler.setFormatter(_LogFormatter(**formatter_kwargs))
    logger.addHandler(file_handler)  # no level split, all levels


# pylint: disable-next=invalid-name
def getLogger(
    name=None,
    *,
    datefmt=_DATEFMT_AUTO,
    relative_to=None,
    disable_color=False,
    disable_diff_only_compression=False,
    filename=None,
    file_mode="a",
    disable_console=False,
    enable_propagate=False,
):
    """
    return a configured :class:`KamiLogger` for ``name``, creating it if
    needed


    :param name: logger name; default=None, the root logger
    :type name: str, optional
    :param datefmt: strftime format for timestamps;
            default depends on the destination: console prints no
            timestamp, the log file uses ``DATEFMT_DATETIME_MS``;
            an explicit value applies to console and file alike,
            ``None`` disables timestamps on both;
            ignored when ``relative_to`` is set
    :type datefmt: str or None, optional
    :param relative_to: Unix timestamp to use as epoch for relative time
            display; mutually exclusive with ``datefmt``; default=None
    :type relative_to: float, optional
    :param disable_color: whether to disable ANSI color on all handlers
            and the diff-only filter; default=False
    :type disable_color: bool, optional
    :param disable_diff_only_compression: whether to turn off diff-only
            compression and pass records through untouched; default=False
    :type disable_diff_only_compression: bool, optional
    :param filename: path to a log file; when set, a file handler using
            the kamilog format is attached, with color always disabled;
            ``None`` attaches no file handler; default=None
    :type filename: str or None, optional
    :param file_mode: open mode for the log file, forwarded to
            ``logging.FileHandler``; default="a" (append)
    :type file_mode: str, optional
    :param disable_console: whether to skip the stdout/stderr handlers,
            yielding a file-only logger; default=False
    :type disable_console: bool, optional
    :param enable_propagate: whether records also propagate to ancestor
            loggers' handlers; default=False
    :type enable_propagate: bool, optional
    :return: the logger named ``name``, created if it does not exist;
            the root logger if ``name`` is ``None``
    :rtype: KamiLogger
    """
    if datefmt is _DATEFMT_AUTO:  # unset: console silent, file full stamp
        console_datefmt, file_datefmt = None, DATEFMT_DATETIME_MS
    else:
        console_datefmt = file_datefmt = datefmt

    logger = logging.getLogger(name)

    if not isinstance(logger, KamiLogger):
        logger.__class__ = KamiLogger

    logger.propagate = enable_propagate

    console_kwargs = {
        "datefmt": console_datefmt,
        "relative_to": relative_to,
        "disable_color": disable_color,
    }
    _attach_diff_only_filter(
        logger, console_kwargs, disable_diff_only_compression
    )
    if not disable_console:
        _attach_console_handlers(logger, console_kwargs)
    if filename is not None:
        file_kwargs = dict(
            console_kwargs, datefmt=file_datefmt, disable_color=True
        )
        _attach_file_handler(logger, filename, file_mode, file_kwargs)

    return logger


# shared parsers  ==============================================================

_common_parser = ArgumentParser(add_help=False)
_newline_group = _common_parser.add_mutually_exclusive_group()
_newline_group.add_argument(
    "-n",
    "--newline",
    dest="newline",
    action="store_true",
    default=None,
    help="always append a trailing newline after output",
)
_newline_group.add_argument(
    "-N",
    "--no-newline",
    dest="newline",
    action="store_false",
    default=None,
    help="never append a trailing newline after output",
)
_no_color_parser = ArgumentParser(add_help=False, parents=[_common_parser])
_no_color_parser.add_argument(
    "-C",
    "--no-color",
    action="store_true",
    help="disable ANSI color output",
)

_line_width_parser = ArgumentParser(add_help=False, parents=[_no_color_parser])
_line_width_parser.add_argument(
    "-w",
    "--line-width",
    type=int,
    default=80,
    metavar="LINE_WIDTH",
    help="total character width of output line; default 80",
)


def _calc_line_end(args, stdin_content=""):
    """
    decide the trailing-newline ``end`` string: stdin's own newline,
    if any, plus one when ``-n`` and none when ``-N``; with neither
    flag the output ends in exactly one newline
    """
    kept = "\n" if stdin_content.endswith("\n") else ""
    if args.newline is True:
        return kept + "\n"
    if args.newline is False:
        return kept
    return "\n"


def _read_stdin_line():
    """
    :return: the next stdin line raw, and without its trailing newline
    :rtype: tuple(str, str)
    """
    raw = sys.stdin.readline()
    return raw, raw.rstrip("\n")


def _print_output(args, text, raw):
    """
    print ``text`` to stdout, ended per ``-n/-N`` and the newline of ``raw``
    """
    print(text, file=sys.stdout, end=_calc_line_end(args, raw))


def _add_subcommand(
    cli_subparser, name, alias, parents, help_text, description, func
):
    """
    :return: new subparser ``name``, with ``func`` as handler unless
            ``None``, and ``alias`` unless empty
    :rtype: argparse.ArgumentParser
    """
    subparser = cli_subparser.add_parser(
        name,
        parents=parents,
        help=help_text,
        description=description,
        formatter_class=RawDescriptionHelpFormatter,
        aliases=[alias] if alias else [],
    )
    if func is not None:
        subparser.set_defaults(func=func)
    return subparser


# logger CLI  ==================================================================


_LOGGER_HELP = "log stdin lines at LEVEL, honoring verbosity threshold"


_LOGGER_DESCRIPTION = _LOGGER_HELP + """

lines are read from stdin, one log record per stdin line;
verbosity threshold decides which records actually print


example:
  echo 'disk full' | kamilog logger error
  echo 'disk full' | kamilog logger error my_module"""

# lowercase level name → numeric level, ascending by severity
_LOGGER_LEVEL_MAP = {
    logging.getLevelName(lvl).lower(): lvl
    for lvl in sorted(
        (DEBUG, INFO, WARNING, ERROR, CRITICAL, *_CustomLogLevel)
    )
}


def _resolve_level_name(name):
    """
    :return: numeric level of the case-insensitive level ``name``;
            ``None`` passes through
    :rtype: int or None
    """
    return None if name is None else _LOGGER_LEVEL_MAP[name.lower()]


# time format Name to strftime string, None disables timestamps
_LOGGER_TIME_FORMAT_MAP = {
    "time": DATEFMT_TIME,
    "time-ms": DATEFMT_TIME_MS,
    "datetime": DATEFMT_DATETIME,
    "datetime-ms": DATEFMT_DATETIME_MS,
    "no-time": None,
}


def _logger_parser_main(args):
    level = _resolve_level_name(args.level)
    datefmt = _LOGGER_TIME_FORMAT_MAP[args.time_format]  # resolve Time fmt
    logger = getLogger(
        args.name,
        datefmt=datefmt,
        disable_color=args.no_color,
        disable_diff_only_compression=args.no_diff_only,
    )
    set_logging_level_by_namespace(
        args, verbosity=args.verbosity, logger=logger
    )
    raw = sys.stdin.read()
    lines = raw.splitlines()
    last_idx = len(lines) - 1
    final_end = _calc_line_end(args, raw)  # final record's own break
    for i, line in enumerate(lines):  # log each stdin Line
        if i == last_idx:  # only the final break is adjustable
            for handler in logger.handlers:
                handler.terminator = final_end
        logger.log(level, line)


def _register_logger_parser(cli_subparser):
    """
    register the ``logger`` subcommand on ``cli_subparser``
    """
    logger_parser = _add_subcommand(
        cli_subparser,
        "logger",
        "l",
        [_no_color_parser],
        _LOGGER_HELP,
        _LOGGER_DESCRIPTION,
        _logger_parser_main,
    )

    logger_parser.add_argument(
        "level",
        choices=list(_LOGGER_LEVEL_MAP),
        help="log level name",
    )
    logger_parser.add_argument(
        "name",
        nargs="?",
        default=None,
        metavar="LOGGER_NAME",
        help="logger name; default=root logger",
    )
    logger_parser.add_argument(
        "-t",
        "--time-format",
        choices=list(_LOGGER_TIME_FORMAT_MAP),
        default="no-time",
        help="timestamp format; default=no-time",
    )

    logger_parser.add_argument(
        "--verbosity",
        type=int,
        default=3,
        metavar="VERBOSITY",
        help="base verbosity offset for level threshold; default=3",
    )
    add_verbose_arguments(logger_parser)

    logger_parser.add_argument(
        "-D",
        "--no-diff-only",
        action="store_true",
        help="disable diff-only message compression",
    )


# Verbosity  ###################################################################

# auxiliaries  =================================================================


def _set_logger_level(level, *, logger=None, logger_name=None):
    """
    set ``level`` on ``logger``, falling back to ``logger_name``
    """
    if logger is None:
        logger = logging.getLogger(logger_name)
    logger.setLevel(level)


# Verbosity Public API  ========================================================

_VERBOSE_FLAG_CHOICES = ("vq", "VQ", "")
_EXTREME_VERBOSITY = 1_000_000

_STEP_VERBOSE_HELP = "increase verbosity by 1 per {opt}"
_STEP_QUIET_HELP = "decrease verbosity by 1 per {opt}"
_EXTREMITY_VERBOSE_HELP = "set maximally verbose"
_EXTREMITY_QUIET_HELP = "set maximally quiet"


def _flag_option_strings(short_flag, long_flag):
    """
    :return: ``[long_flag]``, or ``["-{short_flag}", long_flag]`` when
            ``short_flag`` is truthy
    :rtype: list[str]
    """
    if short_flag:
        return ["-{}".format(short_flag), long_flag]
    return [long_flag]


def _add_step_argument(parser, short_flag, long_flag, help_template):
    """
    add a counting option to ``parser``, its help naming the flags bound
    """
    opts = _flag_option_strings(short_flag, long_flag)
    parser.add_argument(
        *opts,
        action="count",
        default=0,
        help=help_template.format(opt="/".join(opts)),
    )


def _add_extremity_argument(parser, short_flag, long_flag, dest, help_text):
    """
    add an option to ``parser`` that sets ``dest`` to the extreme
    """
    parser.add_argument(
        *_flag_option_strings(short_flag, long_flag),
        dest=dest,
        action="store_const",
        const=_EXTREME_VERBOSITY,
        default=0,
        help=help_text,
    )


def add_verbose_arguments(
    parser,
    *,
    step_flags="vq",
    extremity_flags="VQ",
):
    """
    add verbosity options to ``parser``, in two behaviors:

    - **step** — ``--verbose``/``--quiet``, each occurrence shifts
      verbosity up/down by one
    - **extremity** — ``--max-verbose``/``--max-quiet``, jumps
      straight to the maximum/minimum verbosity

    those four long options are always added. ``step_flags`` and
    ``extremity_flags`` only choose which single-letter short flag, if
    any, is bound alongside each behavior; each takes one of three
    values:

    - ``"vq"`` — bind ``-v`` and ``-q`` as the pair's short flags
    - ``"VQ"`` — bind ``-V`` and ``-Q`` as the pair's short flags
    - ``""`` — bind no short flag; the behavior stays reachable only
      through its long options

    eg the default ``step_flags="vq"``, ``extremity_flags="VQ"`` binds:

    - ``-v``/``-q`` alongside ``--verbose``/``--quiet``
    - ``-V``/``-Q`` alongside ``--max-verbose``/``--max-quiet``

    whereas ``step_flags="VQ"``, ``extremity_flags=""`` binds:

    - ``-V``/``-Q`` alongside ``--verbose``/``--quiet``
    - no short flag alongside ``--max-verbose``/``--max-quiet``


    :param parser: argument parser to extend
    :type parser: argparse.ArgumentParser
    :param step_flags: short-flag pair bound to the step behavior;
            one of ``"vq"``, ``"VQ"``, ``""``; default=``"vq"``
    :type step_flags: str, optional
    :param extremity_flags: short-flag pair bound to the extremity
            behavior; one of ``"vq"``, ``"VQ"``, ``""``;
            default=``"VQ"``
    :type extremity_flags: str, optional
    :raises ValueError: step_flags is not one of ``"vq"``, ``"VQ"``, ``""``
    :raises ValueError: extremity_flags is not one of ``"vq"``, ``"VQ"``,
            ``""``
    :raises ValueError: step_flags and extremity_flags are the same
            non-empty pair, which would bind one flag letter twice
    """
    for param, flags in (
        ("step_flags", step_flags),
        ("extremity_flags", extremity_flags),
    ):
        if flags not in _VERBOSE_FLAG_CHOICES:
            raise ValueError(
                "param {} {!r} must be one of {!r}".format(
                    param, flags, _VERBOSE_FLAG_CHOICES
                )
            )
    if step_flags and step_flags == extremity_flags:
        raise ValueError(
            "param step_flags and extremity_flags conflict: "
            "both are {!r}".format(step_flags)
        )

    v_flag, q_flag = step_flags or ("", "")
    ev_flag, eq_flag = extremity_flags or ("", "")

    _add_step_argument(parser, v_flag, "--verbose", _STEP_VERBOSE_HELP)
    _add_step_argument(parser, q_flag, "--quiet", _STEP_QUIET_HELP)
    _add_extremity_argument(
        parser, ev_flag, "--max-verbose", "verbose", _EXTREMITY_VERBOSE_HELP
    )
    _add_extremity_argument(
        parser, eq_flag, "--max-quiet", "quiet", _EXTREMITY_QUIET_HELP
    )


def calc_verbosity(namespace, *, verbosity=0):
    """
    apply namespace's verbose/quiet counts as an offset to verbosity


    :param namespace: parsed namespace containing ``--verbose`` and/or
            ``--quiet`` counts
    :type namespace: argparse.Namespace
    :param verbosity: base verbosity that namespace's ``--verbose``/``--quiet``
            counts are added to/subtracted from; default=0
    :type verbosity: int, optional
    :return: resulting verbosity after applying namespace's offset
    :rtype: int
    """
    if hasattr(namespace, "verbose"):
        verbosity += namespace.verbose
    if hasattr(namespace, "quiet"):
        verbosity -= namespace.quiet
    return verbosity


# verbosity → level; values beyond ±3 clamp to the ends
_VERBOSITY2LEVEL = {
    3: DEBUG,
    2: ENTER,
    1: INFO,
    0: DONE,
    -1: WARNING,
    -2: ERROR,
    -3: CRITICAL,
}


def calc_logging_level(verbosity, *, namespace=None):
    """
    map a verbosity integer to a logging level, optionally offset by
    namespace's verbose/quiet counts


    :param verbosity: base verbosity integer; higher is more verbose
    :type verbosity: int
    :param namespace: parsed namespace containing ``--verbose`` and/or
            ``--quiet`` counts, applied via :func:`calc_verbosity` to
            offset ``verbosity`` before mapping; default=None
    :type namespace: argparse.Namespace, optional
    :return: logging level corresponding to the resulting verbosity
    :rtype: int
    """
    if namespace is not None:
        verbosity = calc_verbosity(namespace, verbosity=verbosity)

    return _VERBOSITY2LEVEL[max(-3, min(3, verbosity))]


# set logger level  ------------------------------------------------------------


def set_logging_level_by_namespace(
    namespace, *, verbosity=0, logger=None, logger_name=None
):
    """
    set the logging level of a logger based on verbosity flags


    :param namespace: parsed namespace containing ``--verbose`` and/or
            ``--quiet`` counts
    :type namespace: argparse.Namespace
    :param verbosity: base verbosity that namespace's ``--verbose``/``--quiet``
            counts are added to/subtracted from; default=0
    :type verbosity: int, optional
    :param logger: logger instance to configure; default=None
    :type logger: logging.Logger, optional
    :param logger_name: name of logger to configure;
            ``None`` targets the root logger;
            ignored when ``logger`` is provided; default=None
    :type logger_name: str, optional
    """
    _set_logger_level(
        calc_logging_level(verbosity, namespace=namespace),
        logger=logger,
        logger_name=logger_name,
    )


def set_logging_level_by_verbosity(verbosity, *, logger=None, logger_name=None):
    """
    set the logging level of a logger based on a verbosity integer


    :param verbosity: verbosity integer; higher is more verbose
    :type verbosity: int
    :param logger: logger instance to configure; default=None
    :type logger: logging.Logger, optional
    :param logger_name: name of logger to configure;
            ``None`` targets the root logger;
            ignored when ``logger`` is provided; default=None
    :type logger_name: str, optional
    """
    _set_logger_level(
        calc_logging_level(verbosity),
        logger=logger,
        logger_name=logger_name,
    )


# Comment Banner  ##############################################################


_CONTENT_SPACING = "  "
_PADDING_MAP = {1: "#", 2: "=", 3: "*", 4: "+", 5: "-"}


def _resolve_padding_preset(padding):
    """
    :raises ValueError: ``padding`` is an int outside 1~5
    :return: padding char for preset ``padding`` (1~5); any other
            ``padding`` unchanged
    :rtype: str
    """
    if not isinstance(padding, int):
        return padding
    if padding not in _PADDING_MAP:
        raise ValueError("param padding int must be 1~5")
    return _PADDING_MAP[padding]


def _check_banner_content(content, line_width):
    """
    raise ``ValueError`` unless ``content`` is one line fitting ``line_width``
    """
    if "\n" in content:
        raise ValueError("param content must be a single line")
    if len(content) > line_width:
        raise ValueError(
            "param content length {} exceeds line_width {}".format(
                len(content), line_width
            )
        )


def _check_padding_char(padding):
    """
    raise ``ValueError`` unless ``padding`` is one printable non-space char
    """
    if len(padding) != 1:
        raise ValueError("param padding must be a single character")
    if not padding.isprintable() or padding == " ":
        raise ValueError("param padding must be a normal printable character")


def _grey_fill(renderer, padding, n):
    """
    :return: ``padding`` repeated ``n`` times, colored grey
    :rtype: str
    """
    return renderer.color_grey(padding * n)


def _resolve_renderer(renderer, file):
    """
    :return: ``renderer``, or a new one for ``file`` when ``None``
    :rtype: AnsiRenderer
    """
    return AnsiRenderer(file) if renderer is None else renderer


def _gen_comment_banner_generic(
    mode,
    content,
    padding,
    *,
    line_width=80,
    horizontal_offset=0,
    file=sys.stdout,
    renderer=None,
):
    """
    return ``content`` padded to ``line_width``, aligned per ``mode``:
    ``"c"`` centered, ``"l"`` left-justified, ``"r"`` right-justified
    """
    padding = _resolve_padding_preset(padding)
    _check_banner_content(content, line_width)
    _check_padding_char(padding)
    renderer = _resolve_renderer(renderer, file)

    if mode in ("l", "r"):
        remaining = line_width - len(content) - len(_CONTENT_SPACING)
        fill = _grey_fill(renderer, padding, remaining)
        if mode == "l":
            return content + _CONTENT_SPACING + fill
        return fill + _CONTENT_SPACING + content

    # centered; horizontal_offset shifts content: -1 left, +1 right
    remaining = line_width - len(content) - len(_CONTENT_SPACING) * 2
    left = remaining // 2 + horizontal_offset
    right = remaining - left
    if left < 0 or right < 0:
        raise ValueError("param horizontal_offset out of range")
    return (
        _grey_fill(renderer, padding, left)
        + _CONTENT_SPACING
        + content
        + _CONTENT_SPACING
        + _grey_fill(renderer, padding, right)
    )


# Comment Banner Public API  ===================================================


def gen_comment_banner_centered(*args, **kwargs):
    """
    generate a line with ``content`` centered,
    filling both sides with ``padding`` to reach ``line_width``

    when the remaining width is odd, the extra character goes to the right


    :param content: text to pad; must be a single, non-empty line no
            longer than ``line_width``
    :type content: str
    :param padding: single printable non-space fill character, or int 1-5
            (1: #, 2: =, 3: *, 4: +, 5: -)
    :type padding: str or int
    :param line_width: total output width; default=80
    :type line_width: int, optional
    :param horizontal_offset: nudge the centered content sideways by this
            many columns; negative shifts left, positive shifts right;
            default=0
    :type horizontal_offset: int, optional
    :param file: output stream, used only for ANSI TTY detection;
            default=``sys.stdout``
    :type file: IO, optional
    :param renderer: ANSI color renderer;
            if ``None``, created from ``file`` argument; default=None
    :type renderer: AnsiRenderer or None, optional
    :raises ValueError: ``content`` contains ``"\\n"`` or exceeds
            ``line_width``
    :raises ValueError: ``padding`` is not exactly one printable non-space
            character, or is an int outside 1-5
    :raises ValueError: ``horizontal_offset`` pushes either fill side below
            zero
    :return: padded line content
    :rtype: str
    :example:
    >>> gen_comment_banner_centered("hi", "=", line_width=20)
    '=======  hi  ======='
    >>> gen_comment_banner_centered(
    ...     "hi", "=", line_width=20, horizontal_offset=2
    ... )
    '=========  hi  ====='
    >>> gen_comment_banner_centered("hi", 2, line_width=20)
    '=======  hi  ======='
    """
    return _gen_comment_banner_generic("c", *args, **kwargs)


def gen_comment_banner_left_just(*args, **kwargs):
    """
    generate a line with ``content`` left-justified,
    filling the right with ``padding``

    see :func:`gen_comment_banner_centered` for parameter and error
    details


    :return: padded line content
    :rtype: str
    :example:
    >>> gen_comment_banner_left_just("hi", "=", line_width=20)
    'hi  ================'
    >>> gen_comment_banner_left_just("hi", 2, line_width=20)
    'hi  ================'
    """
    return _gen_comment_banner_generic("l", *args, **kwargs)


def gen_comment_banner_right_just(*args, **kwargs):
    """
    generate a line with ``content`` right-justified,
    filling the left with ``padding``

    see :func:`gen_comment_banner_centered` for parameter and error
    details


    :return: padded line content
    :rtype: str
    :example:
    >>> gen_comment_banner_right_just("hi", "=", line_width=20)
    '================  hi'
    >>> gen_comment_banner_right_just("hi", 2, line_width=20)
    '================  hi'
    """
    return _gen_comment_banner_generic("r", *args, **kwargs)


def gen_comment_banner_zero(
    lines, *, line_width=80, file=sys.stdout, renderer=None
):
    """
    generate a multi-line boxed comment banner (CB0)

    wraps each line with `# `, framed by top and bottom `#` rulers


    :param lines: lines to include in the banner
    :type lines: iterable of str
    :param line_width: total output width; default=80
    :type line_width: int, optional
    :param file: output stream, used only for ANSI TTY detection;
            default=``sys.stdout``
    :type file: IO, optional
    :param renderer: ANSI color renderer;
            if ``None``, created from ``file`` argument; default=None
    :type renderer: AnsiRenderer or None, optional
    :raises ValueError: any line contains ``"\\n"`` or exceeds
            ``line_width - 2`` (reserved for `# ` prefix)
    :return: multi-line boxed banner as a string
    :rtype: str
    :example:
    >>> gen_comment_banner_zero(["line 1", "line 2"], line_width=20)
    ####################
    # line 1
    # line 2
    ####################
    """
    renderer = _resolve_renderer(renderer, file)

    ruler = renderer.color_grey("#" * line_width)
    formatted_lines = [ruler]

    for line in lines:
        if "\n" in line:
            raise ValueError("param lines must not contain newlines")
        if len(line) > line_width - 2:
            raise ValueError(
                "param line length {} exceeds line_width - 2 {}".format(
                    len(line), line_width - 2
                )
            )
        formatted_lines.append(renderer.color_grey("# ") + line)

    formatted_lines.append(ruler)
    return "\n".join(formatted_lines)


# comment banner parser  =======================================================

_COMMENT_BANNER_HELP = "print stdin content padded to line width"


_COMMENT_BANNER_DESCRIPTION = _COMMENT_BANNER_HELP + """

content is read from stdin, as a single line

example:
  echo 'hello world' | kamilog cb c '=' -w 20"""


def _comment_banner_parser_main(args):
    mode_map = {"center": "c", "left": "l", "right": "r"}
    mode = mode_map.get(args.mode, args.mode)
    file = sys.stdout
    renderer = AnsiRenderer(file, is_disabled=args.no_color)
    raw, content = _read_stdin_line()
    padding = int(args.padding) if args.padding in "12345" else args.padding
    line = _gen_comment_banner_generic(
        mode,
        content,
        padding,
        line_width=args.line_width,
        file=file,
        renderer=renderer,
    )
    _print_output(args, line, raw)


def _register_comment_banner_parser(cli_subparser):
    """
    register the ``comment_banner`` subcommand on ``cli_subparser``
    """
    comment_banner_parser = _add_subcommand(
        cli_subparser,
        "comment_banner",
        "cb",
        [_line_width_parser],
        _COMMENT_BANNER_HELP,
        _COMMENT_BANNER_DESCRIPTION,
        _comment_banner_parser_main,
    )

    comment_banner_parser.add_argument(
        "mode",
        choices=["c", "l", "r", "center", "left", "right"],
        help=(
            "text alignment: c/center, l/left(-justified), r/right(-justified)"
        ),
    )
    comment_banner_parser.add_argument(
        "padding",
        metavar="PADDING",
        help="fill char, or int 1~5 for CB1~CB5 preset (1:#/2:=/3:*/4:+/5:-)",
    )


# cb0 parser  ==================================================================

_CB0_HELP = "print multi-line boxed comment banner (CB0)"


_CB0_DESCRIPTION = _CB0_HELP + """

lines are read from stdin, one banner line per stdin line

example:
  printf 'line 1\\nline 2\\n' | kamilog cb0 -w 20"""


def _comment_banner_zero_parser_main(args):
    file = sys.stdout
    renderer = AnsiRenderer(file, is_disabled=args.no_color)
    raw = sys.stdin.read()  # all lines from stdin
    lines = raw.splitlines()
    banner = gen_comment_banner_zero(
        lines,
        line_width=args.line_width,
        file=file,
        renderer=renderer,
    )
    _print_output(args, banner, raw)


def _register_comment_banner_zero_parser(cli_subparser):
    """
    register the ``comment_banner_zero`` subcommand on ``cli_subparser``
    """
    _add_subcommand(
        cli_subparser,
        "comment_banner_zero",
        "cb0",
        [_line_width_parser],
        _CB0_HELP,
        _CB0_DESCRIPTION,
        _comment_banner_zero_parser_main,
    )


# color parser  ================================================================

_COLOR_HELP = "print stdin content with ANSI style applied"

_COLOR_DESCRIPTION = _COLOR_HELP + """

content is read from stdin, as a single line

ANSI STYLE:

BOLD UNDERLINE

RED YELLOW GREEN CYAN BLUE MAGENTA
BRIGHT_RED BRIGHT_YELLOW ~~ (8 bright colors)
BLACK GREY WHITE BRIGHT_WHITE

BG_RED BG_BRIGHT_RED BG_BLACK (16 background colors)

example:
  echo 'hello world' | kamilog color RED BOLD"""


def _parse_ansi_style(raw):
    """
    argparse ``type`` adapter for ``AnsiStyle.parse``, mapping an unknown
    member name to ``ArgumentTypeError`` instead of ``ValueError``
    """
    try:
        return AnsiStyle.parse(raw)
    except ValueError as e:
        raise ArgumentTypeError(str(e)) from e


def _print_colored_stdin_line(args, style):
    """
    read a single stdin line, apply ``style``, and print the result,
    honoring ``-n/-N`` via ``args``
    """
    file = sys.stdout
    renderer = AnsiRenderer(file)
    raw, content = _read_stdin_line()
    _print_output(args, renderer.color(content, style), raw)


def _color_parser_main(args):
    style = AnsiStyle(0)
    for s in args.style:
        style |= s
    _print_colored_stdin_line(args, style)


def _register_color_parser(cli_subparser):
    """
    register the ``color`` subcommand on ``cli_subparser``
    """
    color_parser = _add_subcommand(
        cli_subparser,
        "color",
        "c",
        [_common_parser],
        _COLOR_HELP,
        _COLOR_DESCRIPTION,
        _color_parser_main,
    )

    color_parser.add_argument(
        "style",
        metavar="STYLE",
        nargs="+",
        type=_parse_ansi_style,
        help="1+ ANSI styles, v.s.",
    )


# color-grey parser  ===========================================================

_COLOR_GREY_HELP = "print stdin content in grey"

_COLOR_GREY_DESCRIPTION = _COLOR_GREY_HELP + """

equivalent to `color GREY`

content is read from stdin, as a single line

example:
  echo 'hello world' | kamilog color-grey"""


def _color_grey_parser_main(args):
    _print_colored_stdin_line(args, AnsiStyle.GREY)


def _register_color_grey_parser(cli_subparser):
    """
    register the ``color-grey`` subcommand on ``cli_subparser``
    """
    _add_subcommand(
        cli_subparser,
        "color-grey",
        "cg",
        [_common_parser],
        _COLOR_GREY_HELP,
        _COLOR_GREY_DESCRIPTION,
        _color_grey_parser_main,
    )


# deed CLI  ====================================================================
_DEED_HELP = "log one deed, e.g. a file copy, in its fixed wording"
_DEED_DESCRIPTION = _DEED_HELP + """
add '-- COMMAND' to run COMMAND and log its outcome instead: exit status 0
logs success, anything else logs failure, and the status is passed back
"""


def _run_deed_command(command, act):
    """
    run the wrapped `command`; mark `act` failed on a non-zero status
    and return the status as a shell would report it
    """
    try:
        status = subprocess.run(command, check=False).returncode
    except OSError as exc:
        act.fail("{}: {}".format(type(exc).__name__, exc))
        return 127 if isinstance(exc, FileNotFoundError) else 126
    if status < 0:  # killed by signal, as shells report it
        status = 128 - status
    if status:
        act.fail("exit {}".format(status))
    return status


def _deed_parser_main(args):
    deed = args.deed
    tail = args.tail_command
    deed_args = [getattr(args, name) for name in deed.arg_names]
    deed_args = [val for val in deed_args if val is not None]
    if tail is None:
        if args.err_level is not None:
            args.deed_parser.error("--err-level needs a command after '--'")
        if not deed_args:  # only run-command may omit its subject
            args.deed_parser.error(
                "the following arguments are required: {}".format(
                    deed.arg_names[0]
                )
            )
    elif deed.name == "run_command":
        if deed_args:
            args.deed_parser.error("the command is given after '--' only")
        deed_args = [shlex.join(tail)]

    logger = getLogger(disable_color=args.no_color)
    logger.setLevel(logging.DEBUG)  # --level alone decides what shows
    level = _resolve_level_name(args.level)
    err_level = _resolve_level_name(args.err_level)

    if tail is None:
        getattr(logger, deed.name)(*deed_args, level=level)
        return 0
    tracked = getattr(logger.track, deed.name)(
        *deed_args, level=level, err_level=err_level
    )
    with tracked as act:
        status = _run_deed_command(tail, act)
    return status


def _register_deed_parser(cli_subparser):
    """
    register the ``deed`` subcommand, with one sub-subcommand per deed
    """
    deed_parser = _add_subcommand(
        cli_subparser, "deed", None, [], _DEED_HELP, _DEED_DESCRIPTION, None
    )
    deed_parser.set_defaults(func=lambda _: deed_parser.print_help())
    deed_subparser = deed_parser.add_subparsers(title="deeds", metavar="DEED")

    for deed in _DEEDS.values():
        sub_parser = deed_subparser.add_parser(
            deed.name.replace("_", "-"),
            parents=[_no_color_parser],
            help=deed.template,
            description="log the deed ``{}``".format(deed.template),
        )
        for i, name in enumerate(deed.arg_names):
            # the subject is required, except that run-command may take its
            # command after '--'; trailing arguments may be omitted
            is_optional = i > 0 or deed.name == "run_command"
            sub_parser.add_argument(
                name, nargs="?" if is_optional else None, default=None
            )
        sub_parser.add_argument(
            "--level",
            choices=list(_LOGGER_LEVEL_MAP),
            default=None,
            help="level of the success line; default={}".format(
                logging.getLevelName(deed.level)
            ),
        )
        sub_parser.add_argument(
            "--err-level",
            choices=list(_LOGGER_LEVEL_MAP),
            default=None,
            help="level of the failure line, with '-- command'; default={}"
            .format(logging.getLevelName(deed.err_level)),
        )
        sub_parser.set_defaults(
            func=_deed_parser_main,
            deed=deed,
            deed_parser=sub_parser,
            tail_command=None,
        )


# CLI main parser  #############################################################

class _CliArgumentParser(ArgumentParser):
    """
    top-level parser that splits `deed ... -- COMMAND` at the first `--`
    """

    def parse_known_args(self, args=None, namespace=None):
        args = list(sys.argv[1:] if args is None else args)
        if args[:1] != ["deed"] or "--" not in args:
            return super().parse_known_args(args, namespace)
        idx = args.index("--")
        head, tail = args[:idx], args[idx + 1 :]
        if not tail:
            self.error("expected a command after '--'")
        namespace, extras = super().parse_known_args(head, namespace)
        namespace.tail_command = tail
        return namespace, extras


_cli_parser = _CliArgumentParser(
    prog="kamilog[.py]",
    description="kamilog CLI: utilities for formatted output and logging",
)
_cli_parser.set_defaults(func=lambda _: _cli_parser.print_help())
_cli_subparser = _cli_parser.add_subparsers(title="subcommands")


# register subcommands

_register_color_parser(_cli_subparser)
_register_color_grey_parser(_cli_subparser)
_register_comment_banner_parser(_cli_subparser)
_register_comment_banner_zero_parser(_cli_subparser)
_register_logger_parser(_cli_subparser)
_register_deed_parser(_cli_subparser)


# Entry Point  #################################################################


def kamilog_cli_main():
    """
    run the kamilog CLI, dispatching to the parsed subcommand's handler
    """
    parsed_args = _cli_parser.parse_args()
    status = parsed_args.func(parsed_args)
    if status:  # a wrapped command's exit status goes back to the shell
        sys.exit(status)


if __name__ == "__main__":
    kamilog_cli_main()
