"""
Module implementing algorithm for notes detection given in "Discovering Patterns in Musical Sequences".
"""
from collections import defaultdict
from dataclasses import dataclass

from tqdm import tqdm

from music21.note import GeneralNote
from music21.stream import Score


@dataclass(frozen=True)
class Melody:
    index: int
    length: int


def overlap(m1: Melody, m2: Melody) -> bool:
    """
    Returns whether there is overlap between melody 1 and melody 2.
    """
    if m1.index > m2.index:
        return overlap(m2, m1)

    return m1.index + m1.length > m2.index


def detect_melody(score: Score, min_length=1, max_length=None, max_length_difference=1) -> Melody:
    merged_parts: list[GeneralNote] = list(score.parts[0].flatten().notesAndRests)
    for part in score.parts[1:]:
        notes_and_rests = list(part.flatten().notesAndRests)
        merged_parts += notes_and_rests

    md = RepeatedPatternFinder(
        merged_parts,
        min_length=min_length,
        max_length=max_length,
        max_length_difference=max_length_difference
    )
    return md.get_best_melody()


class RepeatedPatternFinder:
    """
    Helper class to implement the notes detection approach.
    """

    SIMILARITY_THRESHOLD = 1

    def __init__(
            self,
            notes,
            min_length=1,
            max_length=None,
            max_length_difference=1,
            min_duration=0,
            max_duration=float('inf')
    ):
        self.notes = list(notes)

        self.min_length = min_length
        self.max_length = max_length or len(self.notes)
        self.max_length_difference = max_length_difference

        self.min_duration = min_duration
        self.max_duration = max_duration

        self._similarity_graph = None

    def get_best_melody(self) -> Melody:
        if self._similarity_graph is None:
            self.set_similarity_graph()

        best_melody = None
        best_prominence = -float('inf')

        for length in range(self.min_length, self.max_length + 1):
            duration = sum([self.notes[i].duration.quarterLength for i in range(length)])
            for index in range(len(self.notes) - length + 1):
                melody = Melody(index, length)
                if (
                    self.min_duration <= duration <= self.max_duration and
                    (prominence := self.prominence(melody)) > best_prominence
                ):
                    best_melody = melody
                    best_prominence = prominence

                if index + length < len(self.notes):
                    next_note_quarter_length = self.notes[index + length].duration.quarterLength
                    duration -= self.notes[index].duration.quarterLength - next_note_quarter_length

        return best_melody

    def set_similarity_graph(self):
        self._similarity_graph = defaultdict(dict)

        # base case
        for i in tqdm(range(0, len(self.notes) - 1), leave=False, desc="Base Case"):
            for j in range(i + 1, len(self.notes)):
                m1 = Melody(i, 0)
                m2 = Melody(j, 0)
                self._similarity_graph[m1][m2] = 0

                for m in range(1, self.max_length_difference + 1):
                    m1e = Melody(i, m)
                    m1p = Melody(i, m - 1)
                    self._similarity_graph[m1e][m2] = self.contribution(i, None) + self._similarity_graph[m1p][m2]

                    m2e = Melody(j, m)
                    m2p = Melody(j, m - 1)
                    self._similarity_graph[m1][m2e] = self.contribution(None, j) + self._similarity_graph[m1][m2p]

        # fill in rest
        for length in range(1, self.max_length):
            for i in tqdm(range(0, len(self.notes) - 1), leave=False, desc=f"Length {length}/{self.max_length}"):
                for j in range(i + 1, len(self.notes)):
                    self.fill_dp(i, j, length, length)

                    ml = min(length + self.max_length_difference, self.max_length)
                    for m in range(length + 1, ml + 1):
                        self.fill_dp(i, j, m, length)
                        self.fill_dp(i, j, length, m)

    def fill_dp(self, i, j, length1, length2):
        m1 = Melody(i, length1)
        m2 = Melody(j, length2)

        m1l = Melody(i, length1 - 1)
        m2l = Melody(j, length2 - 1)

        i1 = m1.index + m1.length - 1
        i2 = m2.index + m2.length - 1

        if not (i1 < len(self.notes) and i2 < len(self.notes)):
            return

        res = self._similarity_graph[m1l][m2l] + self.contribution(i1, i2)
        if abs(m1l.length - m2.length) <= self.max_length_difference:
            res = max(res, self._similarity_graph[m1l][m2] + self.contribution(i1, None))
        if abs(m1.length - m2l.length) <= self.max_length_difference:
            res = max(res, self._similarity_graph[m1][m2l] + self.contribution(None, i2))

        self._similarity_graph[m1][m2] = res

    def prominence(self, m: Melody):
        assert self._similarity_graph is not None

        prominence = 0
        for neighbor, similarity in self._similarity_graph[m].items():
            if similarity > self.SIMILARITY_THRESHOLD and not overlap(m, neighbor):
                prominence += similarity

        return prominence

    def contribution(self, i: int | None, j: int | None):
        if i is None:
            return self.contribution(j, i)
        elif self.notes[i].isRest:
            return 0
        elif j is None or self.notes[j].isRest:
            return 0
        return int(self.notes[i].pitch == self.notes[j].pitch)
