"""
kamilog.py

Lightweight Python logging wrapper with custom log levels, structured output,
ANSI colored logging, verbosity control, line-padding utilities, and CLI.

Q.v. https://github.com/kami-lel/kamilog for Project Main Page
Q.v. https://github.com/kami-lel/kamilog/tree/main/docs for Documentation
"""

from argparse import ArgumentParser
import logging
import sys
import time
from collections import deque
from enum import Enum, IntEnum
from logging import Formatter, StreamHandler

__all__ = (
    "getLogger",
    "KamiLogger",
    "add_verbose_arguments",
    "set_logging_level_by_verbosity",
    # ANSI color
    "AnsiColor",
    "AnsiRenderer",
    # log levels
    "NOTSET",
    "DEBUG",
    "ENTER",
    "SKIP",
    "INFO",
    "PASS",
    "SUCC",
    "DONE",
    "WARNING",
    "ERROR",
    "FAIL",
    "CRITICAL",
    # datetime format constants
    "DATEFMT_TIME",
    "DATEFMT_TIME_MS",
    "DATEFMT_DATETIME",
    "DATEFMT_DATETIME_MS",
    # line padding
    "print_line_padding_centered",
    "print_line_padding_left_just",
    "print_line_padding_right_just",
)


# metadata  ####################################################################
__version__ = "1.8.0"
__author__ = "kamiLeL"


# enum  ########################################################################
class _CustomLogLevel(IntEnum):
    """
    custom log level IntEnum with padded 5-char display name.


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

    ENTER = (11, "ENTER")
    SKIP = (12, "SKIP ")
    SUCC = (15, "SUCC.")
    PASS = (21, "PASS ")
    DONE = (25, "DONE ")
    FAIL = (45, "FAIL ")


# level registration during import
for _lvl in _CustomLogLevel:
    logging.addLevelName(int(_lvl), _lvl.name)


# ANSI Color   #################################################################


class AnsiColor(Enum):  # =====================================================
    """
    ANSI escape code values keyed by color name.
    """

    GREY = "\033[90m"
    CYAN = "\033[36m"
    BRIGHT_CYAN = "\033[96m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_MAGENTA = "\033[95m"

    RESET = "\033[0m"
    BOLD = "\033[1m"


class AnsiRenderer:  # =========================================================
    """
    TTY-aware ANSI color code renderer, detects TTY status at construction


    :param stream: output stream used for TTY detection;
            ``None`` disables color unconditionally
    :type stream: IO or None
    """

    _LEVEL_COLORS = {
        logging.DEBUG: AnsiColor.CYAN,
        _CustomLogLevel.ENTER: AnsiColor.BRIGHT_CYAN,
        _CustomLogLevel.SKIP: AnsiColor.BLUE,
        _CustomLogLevel.SUCC: AnsiColor.GREEN,
        logging.INFO: AnsiColor.BRIGHT_BLUE,
        _CustomLogLevel.PASS: AnsiColor.BRIGHT_GREEN,
        _CustomLogLevel.DONE: AnsiColor.BRIGHT_YELLOW,
        logging.WARNING: AnsiColor.YELLOW,
        logging.ERROR: AnsiColor.RED,
        _CustomLogLevel.FAIL: AnsiColor.BRIGHT_RED,
        logging.CRITICAL: AnsiColor.BRIGHT_MAGENTA,
    }

    def __init__(self, stream=None):
        self._enabled = (
            stream is not None and hasattr(stream, "isatty") and stream.isatty()
        )

    # Public API  **************************************************************

    def color(self, text, color, *, use_bold=False):
        """
        apply ANSI color code to text, optionally with bold.


        :param text: text to colorize
        :type text: str
        :param color: ANSI color to apply
        :type color: AnsiColor
        :param use_bold: whether to apply bold formatting;
                defaults to ``False``
        :type use_bold: bool
        :return: ``text`` with color applied if color is enabled;
                otherwise ``text`` unchanged
        :rtype: str
        """
        if not self._enabled:
            return text

        parts = []
        if use_bold:
            parts.append(AnsiColor.BOLD.value)
        parts.append(color.value)
        parts.append(text)
        parts.append(AnsiColor.RESET.value)
        return "".join(parts)

    def color_level(self, text, levelno):
        """
        apply bold and level-specific ANSI color to ``text``


        :param levelno: numeric log level used to select the color
        :type levelno: int
        """
        color = self._LEVEL_COLORS.get(levelno)
        if color is None:
            return text
        return self.color(text, color, use_bold=True)

    def color_grey(self, text):
        """
        apply bright-black (grey) ANSI color to ``text``
        """
        return self.color(text, AnsiColor.GREY)


# Custom Logging  ##############################################################

# constants  ===================================================================

NOTSET = logging.NOTSET  # 0
DEBUG = logging.DEBUG  # 10
ENTER = _CustomLogLevel.ENTER  # 11
SKIP = _CustomLogLevel.SKIP  # 12
SUCC = _CustomLogLevel.SUCC  # 15
INFO = logging.INFO  # 20
PASS = _CustomLogLevel.PASS  # 21
DONE = _CustomLogLevel.DONE  # 25
WARNING = logging.WARNING  # 30
ERROR = logging.ERROR  # 40
FAIL = _CustomLogLevel.FAIL  # 45
CRITICAL = logging.CRITICAL  # 50


# Datetime Formats  ============================================================
DATEFMT_TIME = "%H:%M:%S"
DATEFMT_TIME_MS = "%H:%M:%S.{ms}"
DATEFMT_DATETIME = "%Y-%m-%d %H:%M:%S"
DATEFMT_DATETIME_MS = "%Y-%m-%d %H:%M:%S.{ms}"


class KamiLogger(logging.Logger):  # ===========================================
    """
    logger subclass extending :class:`logging.Logger` with custom levels.

    provides convenience methods for test and hook workflows;
    obtain instances via :func:`getlogger`
    """

    def enter(self, message, *args, **kwargs):
        """
        log at ``ENTER`` level (11): entering a hook or test case.
        """
        if self.isEnabledFor(_CustomLogLevel.ENTER):
            self._log(
                _CustomLogLevel.ENTER, message, args, stacklevel=2, **kwargs
            )

    def skip(self, message, *args, **kwargs):
        """
        log at ``SKIP`` level (12): skipping a hook or test case.
        """
        if self.isEnabledFor(_CustomLogLevel.SKIP):
            self._log(
                _CustomLogLevel.SKIP, message, args, stacklevel=2, **kwargs
            )

    def pass_(self, message, *args, **kwargs):
        """
        log at ``PASS`` level (21): hook or test case passed.
        """
        if self.isEnabledFor(_CustomLogLevel.PASS):
            self._log(
                _CustomLogLevel.PASS, message, args, stacklevel=2, **kwargs
            )

    def succ(self, message, *args, **kwargs):
        """
        log at ``SUCC`` level (22): task or operation succeeded.
        """
        if self.isEnabledFor(_CustomLogLevel.SUCC):
            self._log(
                _CustomLogLevel.SUCC, message, args, stacklevel=2, **kwargs
            )

    def done(self, message, *args, **kwargs):
        """
        log at ``DONE`` level (25): task or operation completed.
        """
        if self.isEnabledFor(_CustomLogLevel.DONE):
            self._log(
                _CustomLogLevel.DONE, message, args, stacklevel=2, **kwargs
            )

    def fail(self, message, *args, **kwargs):
        """
        log at ``FAIL`` level (45): hook or test case failed.
        """
        if self.isEnabledFor(_CustomLogLevel.FAIL):
            self._log(
                _CustomLogLevel.FAIL, message, args, stacklevel=2, **kwargs
            )


logging.setLoggerClass(KamiLogger)
# root logger exists before setLoggerClass — patch its class directly
logging.root.__class__ = KamiLogger


# log formatting  # ============================================================


_PADDED_LEVELNAME_MAP = {
    logging.DEBUG: "DEBUG",
    _CustomLogLevel.ENTER: _CustomLogLevel.ENTER.display,
    _CustomLogLevel.SKIP: _CustomLogLevel.SKIP.display,
    _CustomLogLevel.SUCC: _CustomLogLevel.SUCC.display,
    logging.INFO: "INFO ",
    _CustomLogLevel.PASS: _CustomLogLevel.PASS.display,
    _CustomLogLevel.DONE: _CustomLogLevel.DONE.display,
    logging.WARNING: "WARN.",
    logging.ERROR: "ERROR",
    _CustomLogLevel.FAIL: _CustomLogLevel.FAIL.display,
    logging.CRITICAL: "CRIT.",
}


class _LogFormatEngine:  # *****************************************************
    """
    core log-line formatting logic, independent of ``logging.Formatter``.


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
        return the count of printable characters before the message text.


        :param record: log record to measure
        :type record: logging.LogRecord
        :return: printable character count of the prefix
        :rtype: int
        """
        name = record.name
        has_name = bool(name and name != "root")

        if self._relative_to is not None:
            ts_len = len(self._fmt_relative(record.created))
        elif self._datefmt:
            plain = time.strftime(
                self._datefmt, time.localtime(record.created)
            ).replace("{ms}", "{:03d}".format(int(record.msecs)))
            ts_len = len(plain)
        else:
            ts_len = 0

        level_len = 5  # always padded/truncated to 5
        space_len = 1 if has_name else 0
        source_len = len(name) + 1 if has_name else 1  # "name:" or ":"

        if ts_len:
            return ts_len + 1 + level_len + space_len + source_len + 1
        return level_len + space_len + source_len + 1

    def format_time(self, record, datefmt=None):
        """
        return the formatted and optionally colored timestamp string.


        :param record: log record
        :type record: logging.LogRecord
        :param datefmt: strftime format override; falls back to ``_datefmt``
        :type datefmt: str or None
        :return: formatted timestamp, or empty string when disabled
        :rtype: str
        """
        if self._relative_to is not None:
            return self._fmt_asctime(self._fmt_relative(record.created))
        elif datefmt or self._datefmt:
            fmt = datefmt or self._datefmt
            asctime = time.strftime(
                fmt, time.localtime(record.created)
            ).replace("{ms}", "{:03d}".format(int(record.msecs)))
            return self._fmt_asctime(asctime)
        return ""

    def build_line(self, record):
        """
        build the main log line from a record's parts.


        :param record: log record to format
        :type record: logging.LogRecord
        :return: formatted log line
        :rtype: str
        """
        asctime = self.format_time(record)
        source = self._fmt_source(record.name)
        space = " " if record.name and record.name != "root" else ""

        if asctime:
            return "{} {}{}{} {}".format(
                asctime,
                self._fmt_level(record.levelno),
                space,
                source,
                record.getMessage(),
            )
        return "{}{}{} {}".format(
            self._fmt_level(record.levelno),
            space,
            source,
            record.getMessage(),
        )

    # helpers  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def _fmt_asctime(self, asctime):
        """color ``asctime`` grey."""
        return self._palette.color_grey(asctime)

    def _fmt_level(self, levelno):
        """build the padded, colored level-name segment."""
        padded = _PADDED_LEVELNAME_MAP.get(levelno, str(levelno).ljust(5)[:5])
        return self._palette.color_level(padded, levelno)

    def _fmt_source(self, name):
        """build the colored source-label segment."""
        if not name or name == "root":
            return self._palette.color_grey(":")
        return "{}{}".format(
            self._palette.color_grey(name),
            self._palette.color_grey(":"),
        )

    def _fmt_relative(self, created):
        """format elapsed time relative to ``_relative_to``."""
        delta = created - self._relative_to
        sign = "-" if delta < 0 else "+"
        delta = abs(delta)
        h, rem = divmod(int(delta), 3600)
        m, s = divmod(rem, 60)
        ms = int((delta % 1) * 1000)
        return "{}{:02d}:{:02d}:{:02d}.{:03d}".format(sign, h, m, s, ms)


class _LogFormatter(Formatter):  # *********************************************
    """
    ``logging.Formatter`` adapter wrapping ``_LogFormatEngine``.


    :param stream: forwarded to ``_AnsiRenderer`` for TTY detection;
            ``None`` disables color
    :type stream: IO or None
    :param datefmt: forwarded to ``_LogFormatEngine``; also passed to
            ``Formatter.__init__`` for stdlib compatibility
    :type datefmt: str or None
    :param relative_to: forwarded to ``_LogFormatEngine``
    :type relative_to: float or None
    """

    def __init__(self, stream=None, *, datefmt=None, relative_to=None):
        super().__init__(datefmt=datefmt)
        self.palette = AnsiRenderer(stream)
        self.engine = _LogFormatEngine(
            self.palette, datefmt=datefmt, relative_to=relative_to
        )

    def formatTime(self, record, datefmt=None):
        """
        delegate timestamp formatting to the engine.


        :param record: log record
        :type record: logging.LogRecord
        :param datefmt: strftime format override
        :type datefmt: str or None
        :return: formatted timestamp, or empty string when disabled
        :rtype: str
        """
        return self.engine.format_time(record, datefmt)

    def format(self, record):
        """
        produce the complete log line, appending exc_info and stack_info.


        :param record: log record
        :type record: logging.LogRecord
        :return: fully formatted log line with optional traceback and
                stack info appended
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


class _DiffOnlyEngine:  # ******************************************************
    """
    engine for diff-only compression of log message text.


    :param formatter: formatter used to measure the prefix width and
            apply ``color_grey`` to compression markers
    :type formatter: _LogFormatter
    :param window: number of prior messages held for comparison
    :type window: int
    """

    _COMPRESSION_BLOCK_SIZE = 8
    _PRESERVED_TRAILING_CHARS = 2
    _COMPRESSION_MARKER = "〃\t"

    def __init__(self, formatter, window=3):
        self._formatter = formatter
        self._history = deque(maxlen=window)
        # _common[i] = shared char at position i across all history,
        # or None where messages diverge or lengths differ
        self._common: list = []

    def _update_common(self):
        """
        recompute ``_common`` from the current ``_history`` window
        """
        history = list(self._history)
        if not history:
            self._common = []
            return
        min_len = min(len(s) for s in history)
        max_len = max(len(s) for s in history)
        common: list = []
        for i in range(max_len):
            if i >= min_len:
                common.append(None)  # position missing in some messages
            else:
                ch = history[0][i]
                common.append(
                    ch if all(s[i] == ch for s in history[1:]) else None
                )
        self._common = common

    def _compress(self, record, message):
        """
        compress positions matching ``_common`` into ``〃\\t`` markers.
        """
        block = self._COMPRESSION_BLOCK_SIZE
        trail = self._PRESERVED_TRAILING_CHARS
        prefix_len = self._formatter.engine.count_prefix_chars(record)
        n_common = len(self._common)
        is_common = [
            i < n_common
            and self._common[i] is not None
            and self._common[i] == ch
            for i, ch in enumerate(message)
        ]
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
                run_e = i
                col_offset = (prefix_len + run_s) % block
                padding = (block - col_offset) % block
                tab_s = run_s + padding
                replaceable = run_e - tab_s - trail
                k = replaceable // block if replaceable > 0 else 0
                if k == 0:
                    result.append(message[run_s:run_e])
                else:
                    result.append(message[run_s:tab_s])
                    result.append(
                        self._formatter.palette.color_grey(
                            self._COMPRESSION_MARKER * k
                        )
                    )
                    result.append(message[tab_s + block * k : run_e])
        return "".join(result)

    def process(self, record):
        """
        process ``record`` and return the (possibly compressed) message.


        :param record: log record being processed
        :type record: logging.LogRecord
        :return: compressed message, or the original during warmup
        :rtype: str
        """
        message = record.getMessage()

        if len(self._history) == self._history.maxlen:
            masked = self._compress(record, message)
        else:
            masked = message

        self._history.append(message)
        self._update_common()
        return masked


class _DiffOnlyMsgFilter(logging.Filter):  # ***********************************
    """
    ``logging.Filter`` adapter that applies ``_DiffOnlyEngine`` to records.


    :param formatter: forwarded to ``_DiffOnlyEngine`` for prefix-width
            measurement; pass ``None`` to disable prefix alignment
    :type formatter: _LogFormatter or None
    :param window: forwarded to ``_DiffOnlyEngine`` as the history
            window size
    :type window: int
    """

    def __init__(self, formatter, window=3):
        super().__init__()
        self._engine = _DiffOnlyEngine(formatter, window)

    def filter(self, record):
        """
        apply diff-only compression to ``record.msg`` in place.


        :param record: log record to mask in place
        :type record: logging.LogRecord
        :return: always ``True``; this filter never drops records
        :rtype: bool
        """
        record.msg = self._engine.process(record)
        record.args = ()
        return True


# Logger Public API  ===========================================================


# pylint: disable-next=invalid-name
def getLogger(name=None, *, datefmt=None, relative_to=None):
    """
    return a configured :class:`KamiLogger` for ``name``, creating it if needed.


    :param name: logger name
    :type name: str, optional
    :param datefmt: strftime format for timestamps; ignored when ``relative_to`` is set;
            defaults to ``None`` (no timestamp)
    :type datefmt: str, optional
    :param relative_to: Unix timestamp to use as epoch for relative time display;
            mutually exclusive with ``datefmt``
    :type relative_to: float, optional
    :return: a logger with the `name`, create if non-existence;
            root logger if `name` is `None`
    :rtype: KamiLogger
    """
    logger = logging.getLogger(name)

    if not isinstance(logger, KamiLogger):
        logger.__class__ = KamiLogger

    if not any(isinstance(f, _DiffOnlyMsgFilter) for f in logger.filters):
        logger.addFilter(
            _DiffOnlyMsgFilter(
                _LogFormatter(
                    sys.stdout, datefmt=datefmt, relative_to=relative_to
                )
            )
        )

    if not logger.handlers:
        stdout_handler = StreamHandler(sys.stdout)
        stdout_handler.setFormatter(
            _LogFormatter(sys.stdout, datefmt=datefmt, relative_to=relative_to)
        )
        stdout_handler.addFilter(lambda r: r.levelno < logging.WARNING)

        stderr_handler = StreamHandler(sys.stderr)
        stderr_handler.setFormatter(
            _LogFormatter(sys.stderr, datefmt=datefmt, relative_to=relative_to)
        )
        stderr_handler.addFilter(lambda r: r.levelno >= logging.WARNING)

        logger.addHandler(stdout_handler)
        logger.addHandler(stderr_handler)

    return logger


# Verbosity  ###################################################################

# verbosity helpers  ===========================================================


def _calc_logging_level_from_verbosity(verbosity):
    """
    map a verbosity integer to a logging level
    """
    if verbosity >= 3:
        return logging.DEBUG
    elif verbosity == 2:
        return SUCC
    elif verbosity == 1:
        return logging.INFO
    elif verbosity == 0:
        return DONE
    elif verbosity == -1:
        return logging.WARNING
    elif verbosity == -2:
        return logging.ERROR
    else:  # verbosity <= -3
        return logging.CRITICAL


def _calc_logging_level_from_verbosity_namespace(namespace):
    """
    extract verbosity from namespace and return the logging level
    """
    verbosity = 0
    if hasattr(namespace, "verbose"):
        verbosity += namespace.verbose
    if hasattr(namespace, "quiet"):
        verbosity -= namespace.quiet
    return _calc_logging_level_from_verbosity(verbosity)


# Verbosity Public API  ========================================================


def add_verbose_arguments(parser):
    """
    add ``-v``/``--verbose`` and ``-q``/``--quiet`` options to ``parser``.


    :param parser: argument parser to extend
    :type parser: argparse.ArgumentParser
    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="make verbose, each -v/--verbose increase verbosity by 1",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="make quiet, each -q/--quiet decrease verbosity by 1",
    )


def set_logging_level_by_verbosity(namespace, *, logger=None, logger_name=None):
    """
    set the logging level of a logger based on verbosity flags.


    :param namespace: parsed namespace containing ``--verbose`` and/or ``--quiet`` counts
    :type namespace: argparse.Namespace
    :param logger: logger instance to configure; takes priority over ``logger_name``
    :type logger: logging.Logger, optional
    :param logger_name: name of logger to configure; ``None`` targets the root logger;
            ignored when ``logger`` is provided
    :type logger_name: str, optional
    """
    if logger is None:
        logger = logging.getLogger(logger_name)
    logger.setLevel(_calc_logging_level_from_verbosity_namespace(namespace))


# Line Padding  ################################################################


_CONTENT_SPACING = "  "


def _print_line_padding_generic(
    mode,
    content,
    padding,
    *,
    line_width=80,
    end="\n",
    file=sys.stdout,
    flush=False,
    renderer=None,
):
    """
    print ``content`` padded to ``line_width``


    :param mode: text alignment:
            ``"c"`` centered, ``"l"`` left-justified, ``"r"`` right-justified
    :type mode: str
    """
    if "\n" in content:
        raise ValueError("param content must be a single line")
    if len(content) > line_width:
        raise ValueError(
            "param content length {} exceeds line_width {}".format(
                len(content), line_width
            )
        )
    if len(padding) != 1:
        raise ValueError("param padding must be a single character")
    if not padding.isprintable() or padding == " ":
        raise ValueError("param padding must be a normal printable character")

    if renderer is None:
        renderer = AnsiRenderer(file)

    if mode == "l":  # left justified
        remaining = line_width - len(content) - len(_CONTENT_SPACING)
        padded_content = (
            content
            + _CONTENT_SPACING
            + renderer.color_grey(padding * remaining)
        )
    elif mode == "r":  # right justified
        remaining = line_width - len(content) - len(_CONTENT_SPACING)
        padded_content = (
            renderer.color_grey(padding * remaining)
            + _CONTENT_SPACING
            + content
        )
    else:  # centered (mode == "c")
        remaining = line_width - len(content) - len(_CONTENT_SPACING) * 2
        left = remaining // 2
        right = remaining - left
        padded_content = (
            renderer.color_grey(padding * left)
            + _CONTENT_SPACING
            + content
            + _CONTENT_SPACING
            + renderer.color_grey(padding * right)
        )

    print(padded_content, end=end, file=file, flush=flush)
    return renderer


# Line Padding Public API  =====================================================


def print_line_padding_centered(*args, **kwargs):
    """
    print ``content`` centered, filling both sides with ``padding`` to
    reach ``line_width``.

    when the remaining width is odd, the extra character goes to the right


    :param content: text to print; must be a single, non-empty line no
            longer than ``line_width``
    :type content: str
    :param padding: single printable non-space fill character
    :type padding: str
    :param line_width: total output width; defaults to ``80``
    :type line_width: int
    :param end: appended after output; defaults to ``"\\n"``
    :type end: str
    :param file: output stream; defaults to ``sys.stdout``
    :type file: IO
    :param flush: forcibly flush the stream; defaults to ``False``
    :type flush: bool
    :param renderer: ANSI color renderer;
            if ``None``, created from ``file`` argument
    :type renderer: AnsiRenderer or None
    :return: ANSI color renderer instance
    :rtype: AnsiRenderer
    :raises ValueError: if ``content`` contains ``"\\n"`` or exceeds
            ``line_width``; if ``padding`` is not exactly one printable
            non-space character
    :example:
    >>> print_line_padding_centered("hi", "=", line_width=20)
    =======  hi  =======
    """
    return _print_line_padding_generic("c", *args, **kwargs)


def print_line_padding_left_just(*args, **kwargs):
    """
    print ``content`` left-justified, filling the right with ``padding``.

    see :func:`print_line_padding_centered` for parameter and error
    details.


    :example:
    >>> print_line_padding_left_just("hi", "=", line_width=20)
    hi  ================
    """
    return _print_line_padding_generic("l", *args, **kwargs)


def print_line_padding_right_just(*args, **kwargs):
    """
    print ``content`` right-justified, filling the left with ``padding``.

    see :func:`print_line_padding_centered` for parameter and error
    details.


    :example:
    >>> print_line_padding_right_just("hi", "=", line_width=20)
    ================  hi
    """
    return _print_line_padding_generic("r", *args, **kwargs)


# CLI  #########################################################################

# main parser  =================================================================

cli_parser = ArgumentParser(
    prog=__name__,
    description="kamilog CLI: utilities for formatted output and logging",
)
cli_parser.set_defaults(func=lambda _: cli_parser.print_help())
cli_subparser = cli_parser.add_subparsers(title="subcommands")

# line padding parser  =========================================================

_LINE_PADDING_DESC = "print content padded to line width"


def _line_padding_parser_main(args):
    mode_map = {"center": "c", "left": "l", "right": "r"}
    mode = mode_map.get(args.mode, args.mode)
    file = sys.stderr if args.stderr else sys.stdout
    _print_line_padding_generic(
        mode,
        args.content,
        args.padding,
        line_width=args.line_width,
        file=file,
    )


line_padding_parser = cli_subparser.add_parser(
    "line_padding",
    help=_LINE_PADDING_DESC,
    description=_LINE_PADDING_DESC,
    aliases=["lp"],
)

line_padding_parser.add_argument(
    "mode",
    choices=["c", "l", "r", "center", "left", "right"],
    help="text alignment: c/center, l/left(-justified), r/right(-justified)",
)
line_padding_parser.add_argument(
    "content",
    metavar="CONTENT",
    help="text to print; must be a single line no longer than line-width",
)
line_padding_parser.add_argument(
    "padding",
    metavar="PADDING",
    help="single printable non-space fill character (e.g., #, -, =)",
)
line_padding_parser.add_argument(
    "-w",
    "--line-width",
    type=int,
    default=80,
    metavar="LINE_WIDTH",
    help="total character width of output line; default 80",
)
line_padding_parser.add_argument(
    "-e",
    "--stderr",
    action="store_true",
    help="print to stderr (instead of stdout)",
)

line_padding_parser.set_defaults(func=_line_padding_parser_main)


# Entry Point  =================================================================
if __name__ == "__main__":
    parsed_args = cli_parser.parse_args()
    parsed_args.func(parsed_args)
