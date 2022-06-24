from typing import List, NamedTuple, Optional, Union

IntFloat = Union[int, float]


class ParserNote(NamedTuple):
    note: str
    octave: Optional[int]
    dur: IntFloat

    def with_octave_offset(self, offset: int):
        """
        Return copy of self if octave offset applied.

        :param offset: Octave offset
        """
        octave = self.octave + offset if self.octave is not None else None
        return type(self)(note=self.note, octave=octave, dur=self.dur)


class GroupingElement(NamedTuple):
    channels: List[int]
    clef: str


ScoreType = List[ParserNote]
ScoresType = List[ScoreType]
GroupingType = List[GroupingElement]
