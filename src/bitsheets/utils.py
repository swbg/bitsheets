import logging
import math
import sys
from typing import Any, List, Optional, Union


class SimpleFilter(logging.Filter):
    def __init__(self, loglevel: int, leq: bool):
        """
        Initialize filter.

        :param loglevel: Decision threshold
        :param leq: Whether to let less or equal levels or higher levels pass
        """
        self.loglevel = loglevel
        self.leq = leq

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records.

        :param record: Log record
        :return: Whether to let the record pass
        """
        if self.leq:
            return record.levelno <= self.loglevel
        else:
            return record.levelno > self.loglevel


def set_up_logging(loglevel: int, filename: str = None) -> None:
    """
    Set up basic logging.

    :param loglevel: Log level
    :param filename: Filename to write log records to
    """
    handlers = []
    if loglevel <= logging.INFO:
        info_handler = logging.StreamHandler(sys.stdout)
        info_filter = SimpleFilter(logging.INFO, True)
        info_handler.addFilter(info_filter)

        warning_handler = logging.StreamHandler(sys.stderr)
        warning_filter = SimpleFilter(logging.INFO, False)
        warning_handler.addFilter(warning_filter)

        handlers.extend([info_handler, warning_handler])
    else:
        handlers.append(logging.StreamHandler())

    if filename is not None:
        handlers.append(logging.FileHandler(filename))

    logging.basicConfig(
        level=loglevel,
        handlers=handlers,
        format="[{asctime}] {levelname} {name}::{funcName}: {message}",
        style="{",
        datefmt="%H:%M:%S",
    )

    for logger in [logging.getLogger(name) for name in logging.root.manager.loggerDict]:
        logger.setLevel(loglevel)


def is_close_to_round(val: Any, ndigits: int = 0, eps: float = 1e-5) -> bool:
    """
    Return whether value is close to rounded value.

    :param val: Value to check
    :param ndigits: Number of digits to round to
    :param eps: Tolerance
    """
    return abs(val - round(val, ndigits)) < eps


def round_if_close(val: Any, ndigits: int = 0, eps: float = 1e-5) -> Any:
    """
    Return rounded value if rounding keeps value within tolerance.

    :param val: Value to round
    :param ndigits: Number of digits to round to
    :param eps: Tolerance
    """
    if is_close_to_round(val, ndigits, eps):
        return round(val, ndigits)
    return val


def align_duration(dur: Optional[float], tuplets: List[int] = [3, 5]):
    """
    Align durations to grid.

    We keep durations as float so this is a little hacky.

    :param dur: The duration to align
    :param tuplets: Tuplets to check
    """
    if dur is None:
        return None

    if is_close_to_round(dur, ndigits=1):
        return round(dur, 1)

    for tuplet_base in tuplets:
        for i in range(1, tuplet_base):
            if math.isclose(dur % 1, i / tuplet_base):
                return dur // 1 + i / tuplet_base

    raise ValueError("Could not align duration to grid")


def parse_index(index: Union[int, str, List[Union[int, str]]], max_len: int):
    """
    Parse collection of integer/string index.

    :param index: Index to parse
    :param max_len: Length of score (for negative indices)
    """
    if isinstance(index, int) or isinstance(index, str):
        index = [index]

    def try_parse_str(s: Union[int, str]):
        if isinstance(s, int):
            return [s]
        fr, to = s.split(">")
        fr, to = int(fr or 0), int(to or max_len)
        return range(fr, to + 1)

    index = [xi for s in index for xi in try_parse_str(s)]

    # Support negative indices
    index = [i if i >= 0 else i + max_len for i in index]

    return index
