from copy import copy, deepcopy
from typing import Dict, List, Tuple, Union

from .types import IntFloat, Note, Score, ScoresType
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

                # Unpack scores if multiple where returned
                if isinstance(scores[i], Tuple):
                    for score in scores[i][1:]:
                        scores.append(score)
                    scores[i] = scores[i][0]

    if "chords" in sheets_config:
        ia, ib = sheets_config["chords"]
        scores.append(make_chords(scores[ia], scores[ib]))

    return scores


def score_dur(score: Score) -> IntFloat:
    """
    Calculate total duration of score.

    :param score: Score to process
    """
    return sum(s.dur for s in score)


def transpose_score_octave(score: Score, offset: int) -> Score:
    """
    Transpose a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    """
    return Score([note.with_octave_offset(offset) for note in score])


def transpose_note_octave(
    score: Score, offset: int, index: Union[int, List[int]]
) -> Score:
    """
    Transpose note(s) at index/indices in a score by the specified octave offset.

    :param score: Score to transpose
    :param offset: Octave offset
    :param index: Note index/indices
    """
    if isinstance(index, int):
        index = [index]

    # Support negative indices
    index = [i if i >= 0 else i + len(score) for i in index]

    return Score(
        [
            note.with_octave_offset(offset) if i in index else copy(note)
            for i, note in enumerate(score)
        ]
    )


def remove_note(score: Score, index: Union[int, List[int]]) -> Score:
    """
    Remove note(s) at index/indices.

    :param score: Score to process
    :param index: Note index/indices
    """
    if isinstance(index, int):
        index = [index]

    # Support negative indices
    index = [i if i >= 0 else i + len(score) for i in index]

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
    score = deepcopy(score)
    new_score = Score([score[0]])

    for note in score[1:]:
        if new_score[-1].note == "r" and note.note == "r":
            combined_dur = new_score[-1].dur + note.dur
            new_score[-1] = new_score[-1].from_dur(combined_dur)
            continue
        new_score.append(note)

    assert score_dur(new_score) == score_dur(score)

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

    assert score_dur(new_score) == score_dur(score)

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

    assert score_dur(new_score) == score_dur(score)

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


def make_chords(scorea: Score, scoreb: Score) -> Score:
    """
    Combine two scores and create chords.

    :param scorea: First score
    :param scoreb: Second score
    """
    new_score = Score()

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


def split_notes(score: Score, index: Union[int, List[int]]) -> Tuple[Score, Score]:
    """
    Remove note(s) at index/indices from score and add to new score.

    :param score: Score to process
    :param index: Index/indices to remove
    """
    if isinstance(index, int):
        index = [index]

    # Support negative indices
    index = [i if i >= 0 else i + len(score) for i in index]

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
