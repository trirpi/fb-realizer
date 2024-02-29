import pytest

from music21.improvedFiguredBass.segment import Segment
from music21.improvedFiguredBass.possibility import Possibility
from music21.improvedFiguredBass.rules import ParallelFifths, HiddenFifth, AvoidDoubling
from music21.pitch import Pitch


@pytest.fixture
def segment() -> Segment:
    s = Segment('D3', '6,4')
    s.set_pitch_names_in_chord()
    s.finish_initialization()
    return s


def test_parallel_fifth_rule():
    _ = None
    pf = ParallelFifths(cost=1)

    p1 = Possibility((Pitch('G4'), Pitch('C4')))
    p2 = Possibility((Pitch('A4'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 1
    p1 = Possibility((Pitch('G4'), Pitch('C4')))
    p2 = Possibility((Pitch('A5'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 1
    p1 = Possibility((Pitch('G4'), Pitch('C4')))
    p2 = Possibility((Pitch('A4'), Pitch('D3')))
    assert pf.get_cost(p1, p2, _, _) == 1
    p1 = Possibility((Pitch('G4'), Pitch('C#4')))
    p2 = Possibility((Pitch('A4'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 0
    p1 = Possibility((Pitch('G4'), Pitch('C4')))
    p2 = Possibility((Pitch('Ab4'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 0


def test_hidden_fifth_rule():
    _ = None
    pf = HiddenFifth(cost=1)

    p1 = Possibility((Pitch('F4'), Pitch('C4')))
    p2 = Possibility((Pitch('A4'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 1
    p1 = Possibility((Pitch('F4'), Pitch('C4')))
    p2 = Possibility((Pitch('A5'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 1
    p1 = Possibility((Pitch('F4'), Pitch('C4')))
    p2 = Possibility((Pitch('A4'), Pitch('D3')))
    assert pf.get_cost(p1, p2, _, _) == 0
    p1 = Possibility((Pitch('F4'), Pitch('C4')))
    p2 = Possibility((Pitch('Ab4'), Pitch('D4')))
    assert pf.get_cost(p1, p2, _, _) == 0


def test_avoid_doubling(segment):
    ad = AvoidDoubling(cost=1)
    assert ad.get_cost(Possibility((Pitch('C3'), Pitch('D4'), Pitch('E4'))), segment) == 0
    assert ad.get_cost(Possibility((Pitch('C3'), Pitch('C3'), Pitch('E4'))), segment) == 1
    assert ad.get_cost(Possibility((Pitch('C3'), Pitch('C4'), Pitch('E4'))), segment) == 1
