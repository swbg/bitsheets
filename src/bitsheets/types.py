from typing import List, NamedTuple, Optional, Union

IntFloat = Union[int, float]


class ParserNote(NamedTuple):
    note: Union[str, List[str]]
    octave: Optional[Union[int, List[int]]]
    dur: IntFloat

    def with_octave_offset(self, offset: int) -> "ParserNote":
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

        return type(self)(**{**self._asdict(), "octave": octave})

    def from_notes(self, *notes: List["ParserNote"]) -> "ParserNote":
        """
        Return copy of self with new note.

        :param notes: Parser notes to combine
        """
        return type(self)(
            **{
                **self._asdict(),
                "note": [n.note for n in notes],
                "octave": [n.octave for n in notes],
            }
        )

    def from_dur(self, dur: IntFloat) -> "ParserNote":
        """
        Return copy of self with new duration.

        :param dur: New duration
        """
        return type(self)(**{**self._asdict(), "dur": dur})


class GroupingElement(NamedTuple):
    channels: List[int]
    clef: str


ScoreType = List[ParserNote]
ScoresType = List[ScoreType]
GroupingType = List[GroupingElement]
