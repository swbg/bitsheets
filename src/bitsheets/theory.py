from .types import Note, ScoresType


def get_circle_of_fifths(mode: str = "major"):
    """
    Get circle of fifths.

    :param mode: Mode
    """
    if mode == "major":
        circle = [Note(note="c", octave=4)]
    elif mode == "minor":
        circle = [Note(note="a", octave=3)]
    else:
        raise ValueError("Expected one of 'major', 'minor' as mode")

    for _ in range(0, 11):
        circle.append(circle[-1].with_semitone_offset(7))
    return circle


def get_major_scale(tonic: Note):
    """
    Get major scale of tonic.

    :param tonic: Base note
    """
    steps = [2, 2, 1, 2, 2, 2, 1]
    scale = [tonic]
    for step in steps:
        scale.append(scale[-1].with_semitone_offset(step))
    return scale


def get_natural_minor_scale(tonic: Note):
    """
    Get natural minor scale of tonic.

    :param tonic: Base note
    """
    steps = [2, 1, 2, 2, 1, 2, 2]
    scale = [tonic]
    for step in steps:
        scale.append(scale[-1].with_semitone_offset(step))
    return scale


def get_most_likely_key(scores: ScoresType):
    """
    Get most likely key for scores.

    :param scores: Scores to analyze
    """
    # Prepare scores
    notes = []
    for score in scores:
        notes.extend([note.note for note in score])

    # Prepare tonics
    def _interleave(l):
        res = [l[0]]
        lenl = len(l)
        for i in range(1, lenl // 2):
            res.append(l[i])
            res.append(l[-i])
        res.append(l[i + 1])
        return res

    major_cl = _interleave(get_circle_of_fifths("major"))
    minor_cl = _interleave(get_circle_of_fifths("minor"))

    tonics = [t for pair in zip(major_cl, minor_cl) for t in pair]

    # Count matches
    max_matches = 0
    best_i = 0
    for i, t in enumerate(tonics):
        scale = get_major_scale(t) if i % 2 == 0 else get_natural_minor_scale(t)
        scale = [note.note for note in scale]
        matches = len(list(filter(lambda n: n in scale, notes)))
        if matches > max_matches:
            max_matches = matches
            best_i = i
            if max_matches == len(notes):
                break

    return tonics[best_i].note, "major" if best_i % 2 == 0 else "minor"
