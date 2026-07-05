"""
kamilog.py

Lightweight Python logging wrapper with custom log levels, structured output,
ANSI colored logging, verbosity control, comment banner utilities, and CLI.

Q.v. https://github.com/kami-lel/kamilog for Project Main Page
Q.v. https://github.com/kami-lel/kamilog/tree/main/docs for Documentation
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
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
    "set_logging_level_by_namespace",
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
    # comment banner
    "gen_comment_banner_centered",
    "gen_comment_banner_left_just",
    "gen_comment_banner_right_just",
    "gen_comment_banner_zero",
)


# metadata  ####################################################################
__version__ = "2.3.0"
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

    ENTER = (15, "ENTER")
    SKIP = (16, "SKIP ")
    SUCC = (17, "SUCC.")
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
ENTER = _CustomLogLevel.ENTER  # 15
SKIP = _CustomLogLevel.SKIP  # 16
SUCC = _CustomLogLevel.SUCC  # 17
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
        log at ``ENTER`` level (15): entering a hook or test case.
        """
        if self.isEnabledFor(_CustomLogLevel.ENTER):
            self._log(
                _CustomLogLevel.ENTER, message, args, stacklevel=2, **kwargs
            )

    def skip(self, message, *args, **kwargs):
        """
        log at ``SKIP`` level (16): skipping a hook or test case.
        """
        if self.isEnabledFor(_CustomLogLevel.SKIP):
            self._log(
                _CustomLogLevel.SKIP, message, args, stacklevel=2, **kwargs
            )

    def succ(self, message, *args, **kwargs):
        """
        log at ``SUCC`` level (17): task or operation succeeded.
        """
        if self.isEnabledFor(_CustomLogLevel.SUCC):
            self._log(
                _CustomLogLevel.SUCC, message, args, stacklevel=2, **kwargs
            )

    def pass_(self, message, *args, **kwargs):
        """
        log at ``PASS`` level (21): hook or test case passed.
        """
        if self.isEnabledFor(_CustomLogLevel.PASS):
            self._log(
                _CustomLogLevel.PASS, message, args, stacklevel=2, **kwargs
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
    :param threshold: number of prior messages held for comparison
    :type threshold: int
    """

    _COMPRESSION_BLOCK_SIZE = 8
    _FALLBACK_TAB_SPAN = 2
    _COMPRESSION_MARKER = "〃\t"
    _MARKER_CHAR = "〃"
    _MARKER_WIDTH = 2  # rendered columns of _MARKER_CHAR
    _LEADER_MARKER_MIN = 4  # leader shorter than this becomes bare "\t"

    def __init__(self, formatter, threshold=3):
        self._formatter = formatter
        self._history = deque(maxlen=threshold)
        # _common[i] = shared char at position i across all history,
        # or None where messages diverge or lengths differ
        self._common: list = []

    def _update_common(self):
        """
        recompute ``_common`` from the current ``_history`` messages
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

    @staticmethod
    def _is_word_char(ch):
        """
        report whether ``ch`` is a word character (``0-9A-Za-z`` or ``-_``)
        """
        return (ch.isascii() and ch.isalnum()) or ch in "-_"

    def _find_cut(self, message, run_s, run_e, prefix_len):
        """
        find cut position ending the replaceable part of a common run.

        scans backward from the run end for the nearest word-boundary
        character (any non-word char); the cut lands on that character
        itself, so the boundary symbol prints intact with the tail.
        the scan reaches back at most ``_FALLBACK_TAB_SPAN`` tab stops,
        falling back to that tab-aligned floor when no boundary exists
        within the span


        :param message: full message text being compressed
        :type message: str
        :param run_s: start index of the common run
        :type run_s: int
        :param run_e: end index (exclusive) of the common run
        :type run_e: int
        :param prefix_len: printable prefix width before the message
        :type prefix_len: int
        :return: cut index in ``[run_s, run_e]``; text before it is
                replaceable, text from it stays printed
        :rtype: int
        """
        block = self._COMPRESSION_BLOCK_SIZE
        col_e = prefix_len + run_e
        floor_col = (col_e // block - self._FALLBACK_TAB_SPAN) * block
        cut_min = max(run_s, floor_col - prefix_len)
        for b in range(run_e - 1, cut_min - 1, -1):
            if not self._is_word_char(message[b]):
                return b
        return cut_min

    def _compress(self, record, message):
        """
        compress positions matching ``_common`` into ``〃\\t`` markers.
        """
        block = self._COMPRESSION_BLOCK_SIZE
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
                cut = self._find_cut(message, run_s, run_e, prefix_len)
                col_offset = (prefix_len + run_s) % block
                padding = (block - col_offset) % block
                tab_s = run_s + padding
                replaceable = cut - tab_s
                k = replaceable // block if replaceable > 0 else 0
                if k == 0:
                    result.append(message[run_s:run_e])
                else:
                    gap = replaceable - block * k
                    # leader: common chars before the first tab stop are
                    # never printed; short ones become a bare tab jump,
                    # longer ones earn their own marker
                    if padding >= self._LEADER_MARKER_MIN:
                        result.append(
                            self._formatter.palette.color_grey(
                                self._COMPRESSION_MARKER
                            )
                        )
                    elif padding > 0:
                        result.append("\t")
                    result.append(
                        self._formatter.palette.color_grey(
                            self._COMPRESSION_MARKER * k
                        )
                    )
                    # partial block: marker + spaces padding to the cut
                    if gap >= self._MARKER_WIDTH:
                        result.append(
                            self._formatter.palette.color_grey(
                                self._MARKER_CHAR
                            )
                        )
                        result.append(" " * (gap - self._MARKER_WIDTH))
                    else:
                        result.append(" " * gap)
                    result.append(message[cut:run_e])
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
    :param threshold: forwarded to ``_DiffOnlyEngine`` as the history
            depth before compression activates
    :type threshold: int
    """

    def __init__(self, formatter, threshold=3):
        super().__init__()
        self._engine = _DiffOnlyEngine(formatter, threshold)

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
def getLogger(name=None, *, datefmt=DATEFMT_TIME, relative_to=None):
    """
    return a configured :class:`KamiLogger` for ``name``, creating it if needed.


    :param name: logger name
    :type name: str, optional
    :param datefmt: strftime format for timestamps;
            default=``DATEFMT_TIME`` (``HH:MM:SS``);
            pass ``None`` to disable timestamps
            ignored when ``relative_to`` is set;
    :type datefmt: str or None, optional
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
        return ENTER
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


def _set_logger_level(level, *, logger=None, logger_name=None):
    """
    set ``level`` on ``logger``, falling back to ``logger_name``
    """
    if logger is None:
        logger = logging.getLogger(logger_name)
    logger.setLevel(level)


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


def set_logging_level_by_namespace(namespace, *, logger=None, logger_name=None):
    """
    set the logging level of a logger based on verbosity flags.


    :param namespace: parsed namespace containing ``--verbose`` and/or ``--quiet`` counts
    :type namespace: argparse.Namespace
    :param logger: logger instance to configure
    :type logger: logging.Logger, optional
    :param logger_name: name of logger to configure;
            ``None`` targets the root logger;
            ignored when ``logger`` is provided
    :type logger_name: str, optional
    """
    _set_logger_level(
        _calc_logging_level_from_verbosity_namespace(namespace),
        logger=logger,
        logger_name=logger_name,
    )


def set_logging_level_by_verbosity(verbosity, *, logger=None, logger_name=None):
    """
    set the logging level of a logger based on a verbosity integer.


    :param verbosity:
    :type verbosity: int
    :param logger: logger instance to configure
    :type logger: logging.Logger, optional
    :param logger_name: name of logger to configure;
            ``None`` targets the root logger;
            ignored when ``logger`` is provided
    :type logger_name: str, optional
    """
    _set_logger_level(
        _calc_logging_level_from_verbosity(verbosity),
        logger=logger,
        logger_name=logger_name,
    )


# Comment Banner  #############################################################


_CONTENT_SPACING = "  "
_PADDING_MAP = {1: "#", 2: "=", 3: "*", 4: "+", 5: "-"}


def _gen_comment_banner_generic(
    mode,
    content,
    padding,
    *,
    line_width=80,
    file=sys.stdout,
    renderer=None,
):
    """
    return ``content`` padded to ``line_width``


    :param mode: text alignment:
            ``"c"`` centered, ``"l"`` left-justified, ``"r"`` right-justified
    :type mode: str
    """
    if isinstance(padding, int):
        if padding not in _PADDING_MAP:
            raise ValueError("param padding int must be 1~5")
        padding = _PADDING_MAP[padding]

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

    return padded_content


# Comment Banner Public API  ==================================================


def gen_comment_banner_centered(*args, **kwargs):
    """
    generate a line with ``content`` centered,
    filling both sides with ``padding`` to reach ``line_width``.

    when the remaining width is odd, the extra character goes to the right


    :param content: text to pad; must be a single, non-empty line no
            longer than ``line_width``
    :type content: str
    :param padding: single printable non-space fill character, or int 1-5
            (1: #, 2: =, 3: *, 4: +, 5: -)
    :type padding: str or int
    :param line_width: total output width; defaults to ``80``
    :type line_width: int
    :param file: output stream, used only for ANSI TTY detection;
            defaults to ``sys.stdout``
    :type file: IO
    :param renderer: ANSI color renderer;
            if ``None``, created from ``file`` argument
    :type renderer: AnsiRenderer or None
    :return: padded line content
    :rtype: str
    :raises ValueError: if ``content`` contains ``"\\n"`` or exceeds
            ``line_width``; if ``padding`` is not exactly one printable
            non-space character or outside range 1-5 if int
    :example:
    >>> gen_comment_banner_centered("hi", "=", line_width=20)
    '=======  hi  ======='
    >>> gen_comment_banner_centered("hi", 2, line_width=20)
    '=======  hi  ======='
    """
    return _gen_comment_banner_generic("c", *args, **kwargs)


def gen_comment_banner_left_just(*args, **kwargs):
    """
    generate a line with ``content`` left-justified,
    filling the right with ``padding``.

    see :func:`gen_comment_banner_centered` for parameter and error
    details.


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
    filling the left with ``padding``.

    see :func:`gen_comment_banner_centered` for parameter and error
    details.


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
    generate a multi-line boxed comment banner (CB0).

    wraps each line with `# `, framed by top and bottom `#` rulers


    :param lines: lines to include in the banner
    :type lines: iterable of str
    :param line_width: total output width; defaults to ``80``
    :type line_width: int
    :param file: output stream, used only for ANSI TTY detection;
            defaults to ``sys.stdout``
    :type file: IO
    :param renderer: ANSI color renderer;
            if ``None``, created from ``file`` argument
    :type renderer: AnsiRenderer or None
    :return: multi-line boxed banner as a string
    :rtype: str
    :raises ValueError: any line contains ``"\\n"`` or exceeds
            ``line_width - 2`` (reserved for `# ` prefix)
    :example:
    >>> gen_comment_banner_zero(["line 1", "line 2"], line_width=20)
    ####################
    # line 1
    # line 2
    ####################
    """
    if renderer is None:
        renderer = AnsiRenderer(file)

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


# CLI  #########################################################################

# main parser  =================================================================

cli_parser = ArgumentParser(
    prog=__name__,
    description="kamilog CLI: utilities for formatted output and logging",
)
cli_parser.set_defaults(func=lambda _: cli_parser.print_help())
cli_subparser = cli_parser.add_subparsers(title="subcommands")

# comment banner parser  =======================================================

_COMMENT_BANNER_HELP = "print stdin content padded to line width"


def _comment_banner_parser_main(args):
    mode_map = {"center": "c", "left": "l", "right": "r"}
    mode = mode_map.get(args.mode, args.mode)
    file = sys.stderr if args.stderr else sys.stdout
    content = sys.stdin.readline().rstrip("\n")  # single line from stdin
    padding = int(args.padding) if args.padding in "12345" else args.padding
    line = _gen_comment_banner_generic(
        mode,
        content,
        padding,
        line_width=args.line_width,
        file=file,
    )
    print(line, file=file)


comment_banner_parser = cli_subparser.add_parser(
    "comment_banner",
    help=_COMMENT_BANNER_HELP,
    description=(
        _COMMENT_BANNER_HELP
        + "\n\ncontent is read from stdin, as a single line\n\n"
        "example:\n"
        "  echo 'hello world' | python kamilog.py cb c '=' -w 20"
    ),
    formatter_class=RawDescriptionHelpFormatter,
    aliases=["cb"],
)

comment_banner_parser.add_argument(
    "mode",
    choices=["c", "l", "r", "center", "left", "right"],
    help="text alignment: c/center, l/left(-justified), r/right(-justified)",
)

comment_banner_parser.add_argument(
    "padding",
    metavar="PADDING",
    help="fill char, or int 1~5 for CB1~CB5 preset (1:#/2:=/3:*/4:+/5:-)",
)
comment_banner_parser.add_argument(
    "-w",
    "--line-width",
    type=int,
    default=80,
    metavar="LINE_WIDTH",
    help="total character width of output line; default 80",
)
comment_banner_parser.add_argument(
    "-e",
    "--stderr",
    action="store_true",
    help="print to stderr (instead of stdout)",
)

comment_banner_parser.set_defaults(func=_comment_banner_parser_main)


# cb0 parser  ==================================================================

_CB0_HELP = "print multi-line boxed comment banner (CB0)"


def _comment_banner_zero_parser_main(args):
    file = sys.stderr if args.stderr else sys.stdout
    lines = sys.stdin.read().splitlines()  # all lines from stdin
    banner = gen_comment_banner_zero(
        lines,
        line_width=args.line_width,
        file=file,
    )
    print(banner, file=file)


comment_banner_zero_parser = cli_subparser.add_parser(
    "comment_banner_zero",
    help=_CB0_HELP,
    description=(
        _CB0_HELP
        + "\n\nlines are read from stdin, one banner line per stdin line\n\n"
        "example:\n"
        "  printf 'line 1\\nline 2\\n' | python kamilog.py cb0 -w 20"
    ),
    formatter_class=RawDescriptionHelpFormatter,
    aliases=["cb0"],
)

comment_banner_zero_parser.add_argument(
    "-w",
    "--line-width",
    type=int,
    default=80,
    metavar="LINE_WIDTH",
    help="total character width of output line; default 80",
)
comment_banner_zero_parser.add_argument(
    "-e",
    "--stderr",
    action="store_true",
    help="print to stderr (instead of stdout)",
)

comment_banner_zero_parser.set_defaults(func=_comment_banner_zero_parser_main)


# Entry Point  =================================================================
if __name__ == "__main__":
    parsed_args = cli_parser.parse_args()
    parsed_args.func(parsed_args)
