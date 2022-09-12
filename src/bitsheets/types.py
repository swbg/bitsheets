from functools import total_ordering
from typing import List, NamedTuple, Optional, Tuple, Union

from .const import NOTES
from .utils import align_duration

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
        if isinstance(note, str):
            assert note in NOTES + ["r"]
            assert (note != "r") != (octave is None)
        else:
            for note_i in note:
                assert note_i in NOTES + ["r"]

            # Remove rests
            no = [(n, o) for n, o in zip(note, octave) if n != "r"]

            if len(no) == 0:
                note = "r"
                octave = None
            else:
                # Remove duplicate notes
                no = list(set(no))
                note = [n for n, _ in no]
                octave = [o for _, o in no]

        self.note = note
        self.octave = octave
        self.dur = align_duration(dur)

    def _as_dict(self):
        return {"note": self.note, "octave": self.octave, "dur": self.dur}

    def with_semitone_offset(self, offset: int) -> "Note":
        """
        Return copy of self with semitone offset applied.

        :param offset: Semitone offset
        """
        if isinstance(self.note, str):
            new_note_idx = NOTES.index(self.note) + offset
            new_note = NOTES[new_note_idx % 12]
        elif isinstance(self.note, list):
            new_note_idx = [NOTES.index(note) + offset for note in self.note]
            new_note = [NOTES[idx % 12] for idx in new_note_idx]
        else:
            raise ValueError("Error occured while processing note")

        octave_offset = new_note_idx // 12
        if isinstance(self.octave, int):
            new_octave = self.octave + octave_offset
        elif isinstance(self.octave, list):
            new_octave = [octave + octave_offset for octave in self.octave]
        else:
            raise ValueError("Error occured while processing note")

        return type(self)(
            **{
                **self._as_dict(),
                "note": new_note,
                "octave": new_octave,
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

    def from_dur(self, dur: IntFloat) -> "Note":
        """
        Return copy of self with new duration.

        :param dur: New duration
        """
        return type(self)(**{**self._as_dict(), "dur": dur})

    @staticmethod
    def from_notes(*notes: List["Note"], dur: Optional[IntFloat] = None) -> "Note":
        """
        Return new note combined from List of notes.

        :param notes: Notes to combine
        """
        if dur is None:
            dur = notes[0].dur
            for n in notes:
                assert n.dur == dur

        return Note(
            note=[n.note for n in notes],
            octave=[n.octave for n in notes],
            dur=dur,
        )

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

    def idx_at_dur(self, dur: IntFloat) -> Tuple[int, float]:
        """
        Return index and cumulative duration of note playing at specified duration.

        :param dur: Duration from beginning of score
        """
        current_dur = 0
        current_idx = 0
        while current_dur < dur:
            if current_idx == len(self.notes):
                break
            current_dur = align_duration(current_dur + self.notes[current_idx].dur)
            current_idx += 1
        else:
            return current_idx, current_dur
        return None, None

    def note_at_dur(self, dur: IntFloat) -> Note:
        """
        Return note playing at specified duration.

        :param dur: Duration from beginning of score
        """
        idx, _ = self.idx_at_dur(dur)
        if idx is None:
            return None
        return self.notes[idx]

    def get_total_dur(self) -> float:
        """
        Return total duration of score.
        """
        return align_duration(sum(s.dur for s in self))

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
