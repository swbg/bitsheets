import logging
import math
from copy import copy, deepcopy
from typing import Dict, List, Tuple, Union

from .const import NOTES
from .types import Note, Score, ScoresType
from .utils import align_duration, is_close_to_round, parse_index, round_if_close

_logger = logging.getLogger(__name__)


def apply_processing(scores: ScoresType, sheets_config: Dict) -> ScoresType:
    """
    Apply processing configuration to scores.

    :param scores: Scores to process
    :param sheets_config: Sheets config with processing info
    """
    scores = copy(scores)

    if "processing" in sheets_config:
        for i in range(len(scores)):
            if i not in sheets_config["processing"]:
                continue

            for op in sheets_config["processing"][i]:
                if isinstance(op, str):
                    op = [op, {}]
                fun, args = op
                scores[i] = globals()[fun](scores[i], **args)

                # Unpack scores if multiple where returned
                if isinstance(scores[i], Tuple):
                    for score in scores[i][1:]:
                        scores.append(score)
                    scores[i] = scores[i][0]

    if "chords" in sheets_config:
        ia, ib = sheets_config["chords"]["channels"]
        scorea, scoreb = scores[ia], scores[ib]
        kwargs = sheets_config["chords"].get("kwargs", {})

        typ = sheets_config["chords"].get("type", "make_chords")
        if typ == "make_chords":
            scores.append(make_chords(scorea, scoreb, **kwargs))
        elif typ == "align_shortest":
            scores.append(align_shortest(scorea, scoreb, **kwargs))
        elif typ == "part_combine":
            scores.append(fuzzy_part_combine(scorea, scoreb, **kwargs))
        else:
            raise ValueError(f"Unknown chords type {typ!r}")

    return scores


def transpose_score_octave(score: Score, offset: int) -> Score:
    """
    Transpose a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    """
    return Score([note.with_octave_offset(offset) for note in score])


def transpose_note_octave(
    score: Score, offset: int, index: Union[int, str, List[Union[int, str]]]
) -> Score:
    """
    Transpose note(s) at index/indices in a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    :param index: Note index/indices
    """
    index = parse_index(index, len(score))

    return Score(
        [
            note.with_octave_offset(offset) if i in index else copy(note)
            for i, note in enumerate(score)
        ]
    )


def remove_note(score: Score, index: Union[int, str, List[Union[int, str]]]) -> Score:
    """
    Remove note(s) at index/indices.

    :param score: Score to process
    :param index: Note index/indices
    """
    index = parse_index(index, len(score))

    return Score(
        [
            Note("r", None, note.dur) if i in index else copy(note)
            for i, note in enumerate(score)
        ]
    )


def combine_rests(score: Score) -> Score:
    """
    Combine successive rests to a single rest.

    :param score: Score to process
    """

    def check_total_durs(scorea: Score, scoreb: Score) -> None:
        dura = scorea.get_total_dur()
        durb = scoreb.get_total_dur()

        if not math.isclose(dura, durb):
            raise ValueError(f"Expected durations to match but got {dura} and {durb}")

    score = deepcopy(score)
    new_score = Score([score[0]])

    for note in score[1:]:
        if new_score[-1].note == "r" and note.note == "r":
            combined_dur = new_score[-1].dur + note.dur
            new_score[-1] = new_score[-1].from_dur(combined_dur)
            continue
        new_score.append(note)

    check_total_durs(new_score, score)

    for note in new_score:
        if note.note == "r":
            note.dur = round_if_close(note.dur)

    check_total_durs(new_score, score)

    return new_score


def combine_irregular_notes(score: Score) -> Score:
    """
    Combine successive irregular-duration notes of same pitch.

    :param score: Score to process
    """
    score = deepcopy(score)
    new_score = Score([score[0]])

    for note in score[1:]:
        if (
            new_score[-1].note != note.note
            or new_score[-1].octave != note.octave
            or (new_score[-1].dur * 2).is_integer()
            or (note.dur * 2).is_integer()
        ):
            new_score.append(note)
            continue

        combined_dur = new_score[-1].dur + note.dur
        if is_close_to_round(combined_dur, 1):
            combined_dur = round(combined_dur, 1)
            new_score[-1] = new_score[-1].from_dur(combined_dur)
        else:
            new_score.append(note)

    assert math.isclose(new_score.get_total_dur(), score.get_total_dur())

    return new_score


def eat_rests(score: Score, max_dur: float = 0.5) -> Score:
    """
    Remove short rests and add duration to preceeding note instead.

    :param score: Score to process
    :param max_dur: Maxiumum duration of rests to remove
    """
    score = deepcopy(score)
    new_score = Score()

    for note in score:
        if note.note == "r" and note.dur <= max_dur:
            combined_dur = new_score[-1].dur + note.dur
            if combined_dur.is_integer():
                new_score[-1] = new_score[-1].from_dur(combined_dur)
                continue

        new_score.append(note)

    assert math.isclose(new_score.get_total_dur(), score.get_total_dur())

    return new_score


def transpose_score_below(score: Score, t_note: str, t_octave: int):
    """
    Transpose all notes in score below threshold in octaves until above threshold.

    :param score: Score to process
    :param t_note: Note threshold
    :param t_octave: Octave threshold
    """
    new_score = Score()

    thresholds = [Note(t_note, o, 0) for o in range(t_octave, 0, -1)]

    for note in score:
        for i in range(len(thresholds)):
            if note >= thresholds[i]:
                break
        new_score.append(note.with_octave_offset(i))

    return new_score


def split_notes(
    score: Score, index: Union[int, str, List[Union[int, str]]]
) -> Tuple[Score, Score]:
    """
    Remove note(s) at index/indices from score and add to new score.

    :param score: Score to process
    :param index: Index/indices to remove
    """
    index = parse_index(index, len(score))

    scorea = Score(
        [
            note if i not in index else Note("r", None, note.dur)
            for i, note in enumerate(score)
        ]
    )
    scoreb = Score(
        [
            note if i in index else Note("r", None, note.dur)
            for i, note in enumerate(score)
        ]
    )

    scorea = combine_rests(scorea)
    scoreb = combine_rests(scoreb)

    return scorea, scoreb


def make_chords(scorea: Score, scoreb: Score, allow_seconds: bool = True) -> Score:
    """
    Combine two scores and create chords.

    :param scorea: First score
    :param scoreb: Second score
    :param allow_seconds: Whether to allow seconds
    """
    new_score = Score()

    assert len(scorea) == len(scoreb)
    assert scorea.get_total_dur() == scoreb.get_total_dur()

    for na, nb in zip(scorea, scoreb):
        assert na.dur == nb.dur

        if na.note == "r":
            new_score.append(copy(nb))
        elif nb.note == "r":
            new_score.append(copy(na))
        else:
            not_second = (
                abs(
                    NOTES.index(na.note) % len(NOTES)
                    - NOTES.index(nb.note) % len(NOTES)
                )
                > 2
            )

            if na.note == nb.note and na.octave == nb.octave:
                new_score.append(copy(na))
            elif allow_seconds or not_second:
                new_score.append(Note.from_notes(na, nb))
            else:
                new_score.append(copy(na))

    return combine_rests(new_score)


def align_shortest(scorea: Score, scoreb: Score, **kwargs) -> Score:
    """
    Combine two scores and create chords. Truncate notes such that.

    - Notes that start at the same time end at the same time
    - Notes end as soon as a following note starts

    :param scorea: First score
    :param scoreb: Second score
    """
    strike_durs = set()
    for score in [scorea, scoreb]:
        current_dur = 0
        for note in score:
            if note.note != "r":
                strike_durs.add(current_dur)
            current_dur = align_duration(current_dur + note.dur)
        strike_durs.add(score.get_total_dur())

    strike_durs = sorted(strike_durs)

    new_scores = []
    for score in [scorea, scoreb]:
        new_score = Score()

        for dur_from, dur_to in zip(strike_durs[:-1], strike_durs[1:]):
            idx, dur = score.idx_at_dur(dur_from)
            if math.isclose(dur, dur_from) and idx < len(score):
                # Note starts playing at current duration
                new_score.append(score[idx].from_dur(dur_to - dur_from))
            else:
                new_score.append(Note("r", None, dur_to - dur_from))

        new_scores.append(new_score)

    return make_chords(*new_scores, **kwargs)


def fuzzy_part_combine(scorea: Score, scoreb: Score, errors: str = "ignore") -> Score:
    """
    Make chords by using notes from two scores but using durations from one score.

    :param scorea: Original score
    :param scoreb: Score to add to original score
    """
    assert errors in ("ignore", "raise")

    scorea = deepcopy(scorea)
    current_dur = 0

    for note in scoreb:
        if note.note != "r":
            idx, dur = scorea.idx_at_dur(current_dur)
            if dur == current_dur:
                scorea[idx] = Note.from_notes(scorea[idx], note, dur=scorea[idx].dur)
            elif errors == "raise":
                _logger.error("Durations do not match")

        current_dur += note.dur

    return scorea
