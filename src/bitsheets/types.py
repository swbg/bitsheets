from functools import total_ordering
from typing import List, NamedTuple, Optional, Union

from .const import NOTES

IntFloat = Union[int, float]


@total_ordering
class Note:
    def __init__(
        self,
        note: Union[str, List[str]],
        octave: Optional[Union[int, List[int]]],
        dur: Optional[IntFloat] = None,
    ):
        """
        Class for representing parser note.

        :param note: Pitch of note within octave
        :param octave: Octave
        :param dur: Note duration
        """
        assert note in NOTES + ["r"]

        self.note = note
        self.octave = octave
        self.dur = dur

    def _as_dict(self):
        return {"note": self.note, "octave": self.octave, "dur": self.dur}

    def with_semitone_offset(self, offset: int) -> "Note":
        """
        Return copy of self with semitone offset applied.

        :param offset: Semitone offset
        """
        new_note_idx = NOTES.index(self.note) + offset
        octave_offset = new_note_idx // 12
        return type(self)(
            **{
                **self._as_dict(),
                "note": NOTES[new_note_idx % 12],
                "octave": self.octave + octave_offset,
            }
        )

    def with_octave_offset(self, offset: int) -> "Note":
        """
        Return copy of self with octave offset applied.

        :param offset: Octave offset
        """
        if self.octave is None:
            octave = None
        elif isinstance(self.octave, int):
            octave = self.octave + offset
        elif isinstance(self.octave, list):
            octave = [o + offset for o in self.octave]
        else:
            raise ValueError("Type of octave must be int or List[int]")

        return type(self)(**{**self._as_dict(), "octave": octave})

    def from_notes(self, *notes: List["Note"]) -> "Note":
        """
        Return copy of self with new note.

        :param notes: Parser notes to combine
        """
        return type(self)(
            **{
                **self._as_dict(),
                "note": [n.note for n in notes],
                "octave": [n.octave for n in notes],
            }
        )

    def from_dur(self, dur: IntFloat) -> "Note":
        """
        Return copy of self with new duration.

        :param dur: New duration
        """
        return type(self)(**{**self._as_dict(), "dur": dur})

    def __iter__(self):
        return iter((self.note, self.octave, self.dur))

    def __eq__(self, other):
        return self.note == other.note and self.octave == other.octave

    def __lt__(self, other):
        if self.octave < other.octave:
            return True
        if self.octave > other.octave:
            return False
        # Octaves are the same
        return NOTES.index(self.note) < NOTES.index(other.note)

    def __repr__(self):
        return f"Note(note={self.note!r}, octave={self.octave!r}, dur={self.dur!r})"


class Score:
    def __init__(self, notes: Optional[List[Note]] = None):
        """
        Class representing score.

        :param notes: Notes of score
        """
        if notes is None:
            notes = []
        self.notes = notes

    def append(self, note: Note):
        """
        Append note.

        :param note: Note to a append
        """
        self.notes.append(note)

    def extend(self, notes: List[Note]):
        """
        Append notes.

        :param note: Notes to a append
        """
        self.notes.extend(notes)

    def __getitem__(self, key: int):
        return self.notes.__getitem__(key)

    def __setitem__(self, key: int, value: Note):
        return self.notes.__setitem__(key, value)

    def __iter__(self):
        return iter(self.notes)

    def __len__(self):
        return self.notes.__len__()

    def idx_at_dur(self, dur: IntFloat) -> int:
        """
        Return index of note playing at spcified duration.

        :param dur: Duration from beginning of score
        """
        current_dur = 0
        current_idx = 0
        while current_dur < dur:
            if current_idx == len(self.notes):
                break
            current_dur += self.notes[current_idx].dur
            current_idx += 1
        else:
            return current_idx
        return None

    def note_at_dur(self, dur: IntFloat) -> Note:
        """
        Return note playing at spcified duration.

        :param dur: Duration from beginning of score
        """
        idx = self.idx_at_dur(dur)
        if idx is None:
            return None
        return self.notes[idx]

    def __repr__(self):
        return (
            "Score([\n    " + ",\n    ".join(repr(note) for note in self.notes) + "\n])"
        )


class GroupingElement(NamedTuple):
    channels: List[int]
    clef: str
    part_combine: bool = False


ScoresType = List[Score]
GroupingType = List[GroupingElement]
