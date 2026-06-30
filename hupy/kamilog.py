"""
kamilog: Customized Logging Output Module

Provides Python loggers with structured output, custom log levels,
ANSI 16-color support, and flexible timestamp options.

Q.v. https://github.com/kami-lel/kamilog
"""

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
__version__ = "1.7.0"
__author__ = "kamiLeL"


# enum  ########################################################################


class _CustomLogLevel(IntEnum):
    """custom log level with padded display name."""

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
    ANSI color renderer; detects TTY at construction time and applies
    color codes through its public methods.

    when ``stream`` is ``None`` or is not a TTY, all coloring methods
    return their input text unchanged.


    :param stream: output stream used for TTY detection; ``None``
            disables color unconditionally
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

        returns the colored text if color is enabled; otherwise
        returns text unchanged.


        :param text: text to colorize
        :type text: str
        :param color: ANSI color to apply
        :type color: AnsiColor
        :param use_bold: whether to apply bold formatting; defaults to
                ``False``
        :type use_bold: bool
        :return: colored text, or ``text`` unchanged when disabled
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
        apply bold and level-specific ANSI color to ``text``.


        :param text: text to colorize
        :type text: str
        :param levelno: numeric log level used to select the color
        :type levelno: int
        :return: colored text, or ``text`` unchanged when disabled
        :rtype: str
        """
        color = self._LEVEL_COLORS.get(levelno)
        if color is None:
            return text
        return self.color(text, color, use_bold=True)

    def color_grey(self, text):
        """apply bright-black (grey) ANSI color to ``text``."""
        return self.color(text, AnsiColor.GREY)


# logger  ######################################################################


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


# datetime formats  ============================================================
DATEFMT_TIME = "%H:%M:%S"
DATEFMT_TIME_MS = "%H:%M:%S.{ms}"
DATEFMT_DATETIME = "%Y-%m-%d %H:%M:%S"
DATEFMT_DATETIME_MS = "%Y-%m-%d %H:%M:%S.{ms}"


class KamiLogger(logging.Logger):  # ===========================================
    """
    Logger subclass extending :class:`logging.Logger` with six additional levels.

    Custom levels (in numeric order between standard ones):

    - ``ENTER`` (11): entering a hook or test case
    - ``SKIP``  (12): skipping a hook or test case
    - ``PASS``  (21): hook or test case passed
    - ``SUCC``  (22): task or operation succeeded
    - ``DONE``  (25): task or operation completed
    - ``FAIL``  (45): hook or test case failed

    Use :func:`getLogger` to obtain a configured instance.
    """

    def enter(self, message, *args, **kwargs):
        """
        Log at ``ENTER`` level (11): entering a hook or test case.

        :param message: log message
        :type message: str
        """
        if self.isEnabledFor(_CustomLogLevel.ENTER):
            self._log(
                _CustomLogLevel.ENTER, message, args, stacklevel=2, **kwargs
            )

    def skip(self, message, *args, **kwargs):
        """
        Log at ``SKIP`` level (12): skipping a hook or test case.

        :param message: log message
        :type message: str
        """
        if self.isEnabledFor(_CustomLogLevel.SKIP):
            self._log(
                _CustomLogLevel.SKIP, message, args, stacklevel=2, **kwargs
            )

    def pass_(self, message, *args, **kwargs):
        """
        Log at ``PASS`` level (21): hook or test case passed.

        :param message: log message
        :type message: str
        """
        if self.isEnabledFor(_CustomLogLevel.PASS):
            self._log(
                _CustomLogLevel.PASS, message, args, stacklevel=2, **kwargs
            )

    def succ(self, message, *args, **kwargs):
        """
        Log at ``SUCC`` level (22): task or operation succeeded.

        :param message: log message
        :type message: str
        """
        if self.isEnabledFor(_CustomLogLevel.SUCC):
            self._log(
                _CustomLogLevel.SUCC, message, args, stacklevel=2, **kwargs
            )

    def done(self, message, *args, **kwargs):
        """
        Log at ``DONE`` level (25): task or operation completed.

        :param message: log message
        :type message: str
        """
        if self.isEnabledFor(_CustomLogLevel.DONE):
            self._log(
                _CustomLogLevel.DONE, message, args, stacklevel=2, **kwargs
            )

    def fail(self, message, *args, **kwargs):
        """
        Log at ``FAIL`` level (45): hook or test case failed.

        :param message: log message
        :type message: str
        """
        if self.isEnabledFor(_CustomLogLevel.FAIL):
            self._log(
                _CustomLogLevel.FAIL, message, args, stacklevel=2, **kwargs
            )


logging.setLoggerClass(KamiLogger)
# root logger exists before setLoggerClass — patch its class directly
logging.root.__class__ = KamiLogger


# log formatting  #=============================================================


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

    builds each log line from its constituent parts — optional timestamp,
    5-char padded level name, source label, and message — applying ANSI
    color codes when enabled. exposed via ``_LogFormatter.engine`` so
    external callers can reach ``count_prefix_chars`` without going
    through the adapter.


    :param palette: color palette controlling ANSI output
    :type palette: _AnsiRenderer
    :param datefmt: strftime format string for wall-clock timestamps;
            ignored when ``relative_to`` is set; ``None`` disables
            timestamps
    :type datefmt: str or None
    :param relative_to: Unix timestamp used as the epoch for relative
            time display; mutually exclusive with ``datefmt``
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

        accounts for the optional timestamp, 5-char padded level name,
        and source label; ANSI escape codes are excluded from the count.


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

        produces the ``LEVEL source: message`` line with optional
        timestamp prefix. does not handle exc_info or stack_info —
        those are appended by the ``_LogFormatter`` adapter.


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
        """
        :param asctime: pre-formatted datetime string
        :type asctime: str
        :return: asctime in grey, or plain if color disabled
        :rtype: str
        """
        return self._palette.color_grey(asctime)

    def _fmt_level(self, levelno):
        """
        :param levelno: numeric logging level
        :type levelno: int
        :return: 5-char padded level name, colored and bold if enabled
        :rtype: str
        """
        padded = _PADDED_LEVELNAME_MAP.get(levelno, str(levelno).ljust(5)[:5])
        return self._palette.color_level(padded, levelno)

    def _fmt_source(self, name):
        """
        :param name: logger name
        :type name: str
        :return: ``"name:"`` in grey, or ``":"`` in grey if name is
                root or absent
        :rtype: str
        """
        if not name or name == "root":
            return self._palette.color_grey(":")
        return "{}{}".format(
            self._palette.color_grey(name),
            self._palette.color_grey(":"),
        )

    def _fmt_relative(self, created):
        """
        :param created: Unix timestamp of the log record
        :type created: float
        :return: elapsed time as ``+HH:MM:SS.mmm`` or ``-HH:MM:SS.mmm``
        :rtype: str
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
    ``logging.Formatter`` adapter wrapping ``_LogFormatEngine``.

    delegates all line-building and timestamp logic to an internal
    ``_LogFormatEngine`` instance exposed via the ``engine`` property.
    the ``_AnsiRenderer`` controlling color output is accessible via
    ``palette``. exc_info and stack_info appending are handled here
    because they depend on ``Formatter.formatException`` and
    ``Formatter.formatStack``.


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

    maintains a sliding window of prior messages; once the window is
    full, compresses character runs common to all of them into ``〃\\t``
    markers aligned to 8-column boundaries from the rendered line start.
    prefix-width measurement and marker coloring use ``formatter``
    directly.


    :param formatter: formatter used to measure the prefix width and
            apply ``color_grey`` to compression markers
    :type formatter: _LogFormatter
    :param window: number of prior messages held for comparison;
            compression activates once this many messages have been seen
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
        compress positions in ``message`` matching ``_common`` into
        ``〃\\t`` markers.

        aligns each marker to the next multiple-of-8 column measured
        from the rendered line start (prefix + message offset); runs
        too short to fit one full block after alignment are kept as-is.


        :param record: log record used to measure the prefix width
        :type record: logging.LogRecord
        :param message: raw message text to compress
        :type message: str
        :return: compressed message string
        :rtype: str
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

        if the history window is not yet full, the raw message is
        returned unchanged. once full, character positions common to
        all history messages are compressed into ``〃\\t`` markers.


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

    delegates all compression logic to an internal ``_DiffOnlyEngine``
    instance; ``filter()`` mutates ``record.msg`` in place with the
    result.


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


# logger Public API  ===========================================================


# pylint: disable-next=invalid-name
def getLogger(name=None, *, datefmt=None, relative_to=None):
    """
    :param name: logger name
    :type name: str
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
    Map a verbosity integer to a logging level.

    - ``3`` or more: ``DEBUG`` (10)
    - ``2``: ``SUCC`` (15)
    - ``1``: ``INFO`` (20)
    - ``0``: ``DONE`` (25)
    - ``-1``: ``WARNING`` (30)
    - ``-2``: ``ERROR`` (40)
    - ``-3`` or less: ``CRITICAL`` (50)

    :param verbosity: net verbosity count (positive = more verbose)
    :type verbosity: int
    :return: logging level constant
    :rtype: int
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
    Extract verbosity from a parsed namespace and return the corresponding
    logging level.

    Verbosity defaults to 0; each ``-v`` adds 1, each ``-q`` subtracts 1.

    :param namespace: parsed namespace containing ``verbose`` and/or ``quiet`` counts
    :type namespace: argparse.Namespace
    :return: logging level constant
    :rtype: int
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
    Add ``-v``/``--verbose`` and ``-q``/``--quiet`` options to ``parser``.

    Each ``-v`` increases verbosity by 1; each ``-q`` decreases by 1.

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
    Set the logging level of a logger based on verbosity flags.

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

    if mode == 1:  # left justified
        remaining = line_width - len(content) - len(_CONTENT_SPACING)
        padded_content = (
            content
            + _CONTENT_SPACING
            + renderer.color_grey(padding * remaining)
        )
    elif mode == 2:  # right justified
        remaining = line_width - len(content) - len(_CONTENT_SPACING)
        padded_content = (
            renderer.color_grey(padding * remaining)
            + _CONTENT_SPACING
            + content
        )
    else:  # centered
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

    when the remaining width is odd, the extra character goes to the right.
    odd remainder example with ``line_width=11``:
    ``==  hi  ===``


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
    return _print_line_padding_generic(0, *args, **kwargs)


def print_line_padding_left_just(*args, **kwargs):
    """
    print ``content`` left-justified, filling the right with ``padding``.

    see :func:`print_line_padding_centered` for parameter and error
    details.


    :example:
    >>> print_line_padding_left_just("hi", "=", line_width=20)
    hi  ================
    """
    return _print_line_padding_generic(1, *args, **kwargs)


def print_line_padding_right_just(*args, **kwargs):
    """
    print ``content`` right-justified, filling the left with ``padding``.

    see :func:`print_line_padding_centered` for parameter and error
    details.


    :example:
    >>> print_line_padding_right_just("hi", "=", line_width=20)
    ================  hi
    """
    return _print_line_padding_generic(2, *args, **kwargs)
