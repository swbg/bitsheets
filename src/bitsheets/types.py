from typing import List, NamedTuple, Optional, Union

IntFloat = Union[int, float]


class ParserNote(NamedTuple):
    note: str
    octave: Optional[int]
    dur: IntFloat

    def with_octave_offset(self, offset: int) -> "ParserNote":
        """
        Return copy of self with octave offset applied.

        :param offset: Octave offset
        """
        octave = self.octave + offset if self.octave is not None else None
        return type(self)(**{**self._asdict(), "octave": octave})

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
