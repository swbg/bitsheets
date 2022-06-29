import logging
import string
from typing import Any, Dict, Tuple

from .types import (
    GroupingElement,
    GroupingType,
    IntFloat,
    ParserNote,
    ScoresType,
    ScoreType,
)
from .utils import is_close_to_round

_logger = logging.getLogger(__name__)


class LilyPondElement:
    pass


class LilyPondNote(LilyPondElement):
    def __init__(self, note: str, octave: int, dur: IntFloat):
        """
        Class representing single lilypond note.

        :param note: Note pitch within octave
        :param octave: Octave
        :param dur: Duration in beats
        """
        assert isinstance(dur, int) or dur.is_integer()

        if note == "r":
            assert octave is None
        else:
            assert octave is not None

        self.note = note
        self.octave = octave

        self.dur = int(dur)
        self.dots = 0
        self.tied = False

    def add_dot(self) -> None:
        """
        Make note dotted.
        """
        self.dots += 1

    def make_tied(self) -> None:
        """
        Tie note to following note.
        """
        assert self.note != "r", "Rests cannot be tied"
        self.tied = True

    def make_untied(self) -> None:
        """
        Untie note from following note.
        """
        self.tied = False

    def __str__(self):
        if self.note == "r":
            octave_mod = ""
        else:
            octave_mod = max(0, self.octave) * "'" + abs(min(0, self.octave)) * ","
        return (
            self.note + octave_mod + str(self.dur) + self.dots * "." + self.tied * "~"
        )

    def __repr__(self):
        return (
            f"LilyPondNote(note={self.note!r}, "
            f"octave={self.octave!r}, dur={self.dur!r}, "
            f"dots={self.dots!r}, tied={self.tied!r})"
        )


class LilyPondBar(LilyPondElement):
    def __init__(self):
        """
        Class representing lilypond bar.
        """
        self.bar = "|"

    def make_end(self, repeat: bool = False) -> None:
        """
        Convert to end-of-staff bar.

        :param repeat: Whether to add repeat dots.
        """
        if repeat:
            self.bar = r'\bar ":|."'
        else:
            self.bar = r'\bar "|."'

    def __str__(self):
        return self.bar + "\n"

    def __repr__(self):
        return f"LilyPondBar({self.bar!r})"


class LilyPondCommand(LilyPondElement):
    def __init__(self, cmd: str):
        """
        Class representing arbitrary lilypond command.

        :param cmd: Command string
        """
        self.cmd = cmd

    def __str__(self):
        return self.cmd

    def __repr__(self):
        return f"LilyPondCommand({self.cmd!r})"


def parse_grouping(sheets_config: Dict) -> GroupingType:
    """
    Parse grouping config from sheets config.

    :param sheets_config: Sheets config with grouping info
    """
    return [GroupingElement(**config) for config in sheets_config["grouping"]]


def _get_lilypond_header(**kwargs) -> str:
    header_args = {"tagline": "www.lilypond.org"}
    header_args.update(kwargs)

    out = "\\header {\n"
    for k, v in header_args.items():
        if k == "dedication":
            # Add extra space
            out += f' {k}=\\markup {{ \\center-column {{ "{v}" \\vspace #1 }} }}\n'
        else:
            out += f' {k}="{v}"\n'
    return out + "}"


def _get_lilypond_paper(**kwargs) -> str:
    paper_args = {
        "indent": 0,
        "top-margin": 15,
        "bottom-margin": 15,
        "left-margin": 12,
        "right-margin": 12,
    }
    paper_args.update(kwargs)

    out = "\\paper {\n"
    for k, v in paper_args.items():
        out += f" {k}={v}\n"
    return out + "}"


def _check_tuplet(val: IntFloat, mul: int, bar_length: int):
    val_mul = val * (mul / (mul - 1))
    if is_close_to_round(val_mul):
        val_mul = round(val_mul)

        i = bar_length
        while i >= 2.0:
            if val_mul == i:
                return i
            i /= 2
    return None


def _get_biggest_divisor(
    val: IntFloat, current_length: int, bar_length: int
) -> Tuple[IntFloat, IntFloat]:
    assert (bar_length & (bar_length - 1)) == 0  # require power of 2

    # Check for triplets
    triplet = _check_tuplet(val, 3, bar_length)
    if triplet is not None:
        return triplet, -3

    # Check regular lengths
    current_length -= bar_length * (current_length // bar_length)
    across_bars = max(0, (current_length + val) - bar_length)
    val -= across_bars

    i = bar_length
    while i >= 0.5:
        if val >= i:
            return i, val - i + across_bars
        i /= 2

    raise ValueError(f"Could not find biggest divisor for {val}")


def _get_lilypond_staff(
    score: ScoreType,
    octave_offset: int,
    bar_length: int = 16,
    beats_per_whole: int = 16,
    repeat: bool = False,
    anacrusis: int = 0,
    fill_end: bool = True,
    time_base: int = 4,
) -> str:
    """
    Convert score to lilypond format.

    :param score: Score to convert
    :param octave_offset: Relative up/down transposition by an octave
    :param bar_length: Length of a bar in beats
    :param beats_per_whole: Beats per whole note
    :param repeat: Whether to add repeat at end of staff
    :param anacrusis: Anacrusis/pickup in beats
    :param fill_end: Whether to fill the end with rests up to the next full bar
    :param time_base: Base duration for time signature
    """
    notes = []
    total_dur = 0

    time_multiplier = bar_length / beats_per_whole
    notes.append(
        LilyPondCommand(f"\\time {time_base * time_multiplier:.0f}/{time_base}\n")
    )

    if anacrusis > 0:
        assert anacrusis < bar_length
        total_dur = -anacrusis
        lp_anacrusis = beats_per_whole / anacrusis
        assert lp_anacrusis.is_integer()
        notes.append(LilyPondCommand(f"\\partial {int(lp_anacrusis)}"))

    # Keep track of tuplets
    tuplet_cnt = None
    tuplet_len = None

    def _add_lilypond_note(note: ParserNote):
        nonlocal total_dur
        nonlocal tuplet_cnt
        nonlocal tuplet_len

        octave = note.with_octave_offset(octave_offset).octave

        div = 0  # current duration of note written
        rem = note.dur  # remaning duration of note
        while rem > 0:
            div_prev = div
            # Determine longest part of note we could write
            div, rem = _get_biggest_divisor(rem, total_dur, bar_length)

            if tuplet_len is None and rem < 0:
                tuplet_cnt = -rem
                tuplet_len = -rem
                notes.append(
                    LilyPondCommand(
                        f"\\tuplet {tuplet_len:.0f}/{tuplet_len - 1:.0f} {{"
                    )
                )

            if tuplet_len is not None:
                assert -rem == tuplet_len
                tuplet_cnt -= 1

            if div == div_prev / 2:
                if total_dur % bar_length == 0:
                    # Across bars
                    notes.append(
                        LilyPondNote(note.note, octave, dur=beats_per_whole / div)
                    )
                else:
                    notes[-1].make_untied()
                    notes[-1].add_dot()
            else:
                notes.append(LilyPondNote(note.note, octave, dur=beats_per_whole / div))

            # Add tie
            if rem > 0 and note.note != "r":
                notes[-1].make_tied()

            if tuplet_len is not None:
                # Correct before adding to total_dur
                div *= (tuplet_len - 1) / tuplet_len

            total_dur += div

            if tuplet_cnt == 0:
                # Close tuplet
                assert is_close_to_round(total_dur, 1)
                total_dur = round(total_dur, 1)
                tuplet_cnt = None
                tuplet_len = None
                notes.append(LilyPondCommand("}"))

            if total_dur % bar_length == 0:
                notes.append(LilyPondBar())

    for note in score:
        _add_lilypond_note(note)

    if anacrusis > 0 and repeat:
        # Handle anacrusis
        lp_anacrusis = beats_per_whole / anacrusis
        assert lp_anacrusis.is_integer()
        lpc = LilyPondCommand(f"\\partial {int(lp_anacrusis)}")
        notes.append(lpc)

        total_dur += anacrusis
        if total_dur % bar_length == 0:
            notes.append(LilyPondBar())

    if fill_end and total_dur % bar_length != 0:
        rem_dur = bar_length - total_dur % bar_length
        _add_lilypond_note(ParserNote(note="r", octave=None, dur=rem_dur))

    assert isinstance(notes[-1], LilyPondBar)
    notes[-1].make_end(repeat)

    _logger.info("Staff with total duration %d", total_dur)

    return "{\n " + " ".join(str(note) for note in notes) + "}"


def _get_lilypond_grouping(grouping: GroupingType, midi: bool = True) -> str:
    """
    Get lilypond staff grouping.

    :param grouping: List of list with voices per staff
    """
    abc = string.ascii_uppercase
    out = "\\score {\n \\new GrandStaff <<"
    for staff in grouping:
        out += (
            f"\n  \\new Staff {{\\clef {staff.clef} <<"
            + " \\\\ ".join([f"\\channel{abc[i]}" for i in staff.channels])
            + ">>}"
        )
    out += "\n >>"
    if midi:
        out += "\n \\midi {}"
    return out + "\n}"


def dump_scores_lilypond(
    scores: ScoresType,
    pth: str,
    grouping: list,
    octave_offset: int = -3,
    midi: bool = False,
    header_args: Dict[str, Any] = None,
    staff_args: Dict[str, Any] = None,
    paper_args: Dict[str, Any] = None,
) -> None:
    """
    Dump score to lilypond file.

    :param scores: Scores to dump
    :param pth: Output path
    :param header_elems: Info to add to lilypond header
    :param grouping: Staff grouping
    :param midi: Whether to request midi output
    :param staff_args: Staff arguments
    """
    with open(pth, "w") as f:
        f.write('\\version "2.22.2"')
        f.write("\n" + _get_lilypond_paper(**(paper_args or {})))
        f.write("\n" + _get_lilypond_header(**(header_args or {})))

        abc = string.ascii_uppercase
        channels = [voice for staff in grouping for voice in staff.channels]
        for i, score in enumerate(scores):
            if i in channels:  # skip voices that are not in grouping
                staff = _get_lilypond_staff(score, octave_offset, **(staff_args or {}))
                f.write(f"\nchannel{abc[i]} = {staff}")

        f.write("\n" + _get_lilypond_grouping(grouping, midi=midi))
