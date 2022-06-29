from copy import copy, deepcopy
from typing import Dict

from .types import IntFloat, ScoresType, ScoreType
from .utils import is_close_to_round


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

    if "chords" in sheets_config:
        ia, ib = sheets_config["chords"]
        scores.append(make_chords(scores[ia], scores[ib]))

    return scores


def score_dur(score: ScoreType) -> IntFloat:
    """
    Calculate total duration of score.

    :param score: Score to process
    """
    return sum(s.dur for s in score)


def transpose_score_octave(score: ScoreType, offset: int) -> ScoreType:
    """
    Transpose a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    """
    return [note.with_octave_offset(offset) for note in score]


def transpose_note_octave(score: ScoreType, offset: int, index: int) -> ScoreType:
    """
    Transpose single note in a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    :param index: Note index
    """
    return [
        copy(note) if i != index else note.with_octave_offset(offset)
        for i, note in enumerate(score)
    ]


def combine_rests(score: ScoreType) -> ScoreType:
    """
    Combine successive rests to a single rest.

    :param score: Score to process
    """
    score = deepcopy(score)
    new_score = [score[0]]

    for note in score[1:]:
        if new_score[-1].note == "r" and note.note == "r":
            combined_dur = new_score[-1].dur + note.dur
            new_score[-1] = new_score[-1].from_dur(combined_dur)
            continue
        new_score.append(note)

    assert score_dur(new_score) == score_dur(score)

    return new_score


def combine_irregular_notes(score: ScoreType) -> ScoreType:
    """
    Combine successive irregular-duration notes of same pitch.

    :param score: Score to process
    """
    score = deepcopy(score)
    new_score = [score[0]]

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

    assert score_dur(new_score) == score_dur(score)

    return new_score


def eat_rests(score: ScoreType, max_dur: float = 0.5) -> ScoreType:
    """
    Remove short rests and add duration to preceeding note instead.

    :param score: Score to process
    :param max_dur: Maxiumum duration of rests to remove
    """
    score = deepcopy(score)
    new_score = []

    for note in score:
        if note.note == "r" and note.dur <= max_dur:
            combined_dur = new_score[-1].dur + note.dur
            if combined_dur.is_integer():
                new_score[-1] = new_score[-1].from_dur(combined_dur)
                continue

        new_score.append(note)

    assert score_dur(new_score) == score_dur(score)

    return new_score


def make_chords(scorea: ScoreType, scoreb: ScoreType) -> ScoreType:
    """
    Combine two scores and create chords.

    :param scorea: First score
    :param scoreb: Second score
    """
    new_score = []

    assert len(scorea) == len(scoreb)
    assert score_dur(scorea) == score_dur(scoreb)

    for na, nb in zip(scorea, scoreb):
        assert na.dur == nb.dur

        if na.note == "r":
            new_score.append(copy(na))
        elif nb.note == "r":
            new_score.append(copy(nb))
        else:
            new_score.append(na.from_notes(na, nb))

    return new_score
