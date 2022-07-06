import json

from mido import Message, MidiFile, MidiTrack

from .const import NOTES
from .types import ScoresType


def get_midi_note(note: str, octave: int) -> int:
    """
    Convert score note to MIDI note index.

    :param note: Score note
    :param octave: Score octave
    """
    if note not in NOTES or octave is None:
        return -1
    return 12 + 12 * octave + NOTES.index(note)


def get_piano_note(note: str, octave: int) -> int:
    """
    Convert score note to piano key index.

    :param note: Score note
    :param octave: Score octave
    """
    if note not in NOTES or octave is None:
        return -1
    return get_midi_note(note, octave) - 21


def dump_scores_json(scores: ScoresType, pth: str) -> None:
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


def dump_scores_midi(
    scores: ScoresType, pth: str, dur_multiplier: int = 128, velocity: int = 64
) -> None:
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
