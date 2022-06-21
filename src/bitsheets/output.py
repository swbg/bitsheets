import json
import logging
import string
from typing import Dict, Union

from mido import Message, MidiFile, MidiTrack

from .const import NOTES
from .types import GroupingType, ScoresType, ScoreType

_logger = logging.getLogger(__name__)


def get_midi_note(note: str, octave: int):
    """
    Convert score note to MIDI note index.

    :param note: Score note
    :param octave: Score octave
    """
    if note not in NOTES or octave is None:
        return -1
    return 12 + 12 * octave + NOTES.index(note)


def get_piano_note(note: str, octave: int):
    """
    Convert score note to piano key index.

    :param note: Score note
    :param octave: Score octave
    """
    if note not in NOTES or octave is None:
        return -1
    return get_midi_note(note, octave) - 20


def transpose_octave(score: ScoreType, offset: int):
    """
    Transpose a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    """
    return [(n[0], (n[1] + offset) if n[1] is not None else None, n[2]) for n in score]


def dump_score_json(scores: ScoresType, pth: str):
    """
    Dump scores to JSON file.

    :param scores: Scores to dump
    :param pth: Output path
    """
    with open(pth, "w") as f:
        json.dump(
            [
                [[get_piano_note(note, octave), dur] for note, octave, dur in score]
                for score in scores
            ],
            f,
            indent=2,
        )


def dump_score_midi(
    scores: ScoresType, pth: str, dur_multiplier: int = 128, velocity: int = 64
):
    """
    Dump scores to MIDI file.

    :param scores: Scores to dump
    :param pth: Output path
    :param dur_multiplier: Conversion multiplier from score speed to MIDI speed
    :param velocity: MDID stroke velocity
    """
    outfile = MidiFile(type=1)

    delta = 0
    for score in scores:
        track = MidiTrack()
        outfile.tracks.append(track)

        for note, octave, dur in score:
            duration = int(dur_multiplier * dur)
            if note not in NOTES:
                delta += duration
                continue
            else:
                midi_note = get_midi_note(note, octave)
                track.append(
                    Message("note_on", note=midi_note, velocity=velocity, time=delta)
                )
                delta = 0
                track.append(
                    Message(
                        "note_off", note=midi_note, velocity=velocity, time=duration
                    )
                )

    outfile.save(pth)


def _get_lilypond_header(header_elems: Dict[str, str]):
    out = "\\header {"
    for k, v in header_elems.items():
        out += f'{k}="{v}" '
    out = out[:-1] + "}"
    return out


def _get_biggest_divisor(
    val: Union[int, float], current_length: int, bar_length: int = 16
):
    current_length -= bar_length * (current_length // bar_length)
    across_bars = max(0, (current_length + val) - bar_length)
    val -= across_bars

    for i in [16, 8, 4, 2, 1, 0.5]:
        if val >= i:
            return i, val - i + across_bars
    raise ValueError(f"Could not find biggest divisor for {val}")


def _get_lilypond_staff(score: ScoreType, octave_offset: int):
    """
    Convert score to lilypond format.

    :param score: Score to convert
    """
    total_dur = 0
    notes = []

    for note in score:
        if note[1] is not None:
            # Note
            octave = note[1] - octave_offset
            octave_mod = max(0, octave) * "'" + abs(min(0, octave)) * ","
        else:
            # Pause
            octave_mod = ""

        div = 0
        rest = note[2]
        while rest > 0:
            div_prev = div
            div, rest = _get_biggest_divisor(rest, total_dur, 16)

            if div == div_prev / 2:
                if notes[-1] == "|\n":
                    # Across bars
                    notes[-2] += "("
                    notes.append(note[0] + octave_mod + str(int(16 / div)) + ")")
                else:
                    notes[-1] += "."
            else:
                notes.append(note[0] + octave_mod + str(int(16 / div)))

            total_dur += div
            if total_dur % 16 == 0:
                notes.append("|\n")

    _logger.info("Staff with total duration %d", total_dur)

    return "{\n " + " ".join(notes) + "}"


def _get_lilypond_grouping(grouping: GroupingType):
    """
    Get lilypond staff grouping.

    :param grouping: List of list with voices per staff
    """
    abc = string.ascii_uppercase
    out = "<<"
    for staff in grouping:
        out += (
            "\n \\new Staff <<"
            + " \\\\ ".join([f"\\channel{abc[i]}" for i in staff])
            + ">>"
        )
    return out + "\n>>"


def dump_score_lilypond(
    scores: ScoresType,
    pth: str,
    header_elems: dict,
    grouping: list,
    octave_offset: int = 3,
):
    """
    Dump score to lilypond file.

    :param scores: Scores to dump
    :param pth: Output path
    :param header_elems: Info to add to lilypond header
    :param grouping: Staff grouping
    """
    with open(pth, "w") as f:
        f.write('\\version "2.22.2"')
        f.write("\n" + _get_lilypond_header(header_elems))

        abc = string.ascii_uppercase
        voices = [voice for staff in grouping for voice in staff]
        for i, score in enumerate(scores):
            if i in voices:  # skip voices that are not in grouping
                f.write(
                    f"\nchannel{abc[i]} = {_get_lilypond_staff(score, octave_offset)}"
                )
        f.write(_get_lilypond_grouping(grouping))
