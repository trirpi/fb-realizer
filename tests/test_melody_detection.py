from pathlib import Path

import pytest

from music21 import converter
from music21.note import Note
from melody_detection import RepeatedPatternFinder, Melody, detect_melody


@pytest.fixture
def notes():
    return [Note('C4'), Note('D4'), Note('E4'), Note('C4'), Note('F5'),
            Note('C4'), Note('D4'), Note('E4'), Note('C4'), Note('G4'),
            Note('C3'), Note('D3'), Note('E3'), Note('C3')]


@pytest.fixture
def rpf(notes):
    return RepeatedPatternFinder(notes, max_length_difference=2)


def test_contribution_detection(rpf):
    assert rpf.contribution(0, 5) == 1
    assert rpf.contribution(0, 10) == 0
    assert rpf.contribution(0, 1) == 0


def test_similarity(rpf):
    rpf.set_similarity_graph()
    m1 = Melody(1, 2)
    m2 = Melody(3, 2)
    assert rpf._similarity_graph[m1][m2] == 0

    m1 = Melody(0, 2)
    m2 = Melody(5, 2)
    assert rpf._similarity_graph[m1][m2] == 2

    m1 = Melody(1, 3)
    m2 = Melody(6, 3)
    assert rpf._similarity_graph[m1][m2] == 3

    m1 = Melody(1, 3)
    m2 = Melody(6, 4)
    assert rpf._similarity_graph[m1][m2] == 3

    m1 = Melody(4, 3)
    m2 = Melody(9, 3)
    assert rpf._similarity_graph[m1][m2] == 0


def test_max_difference(notes):
    rpf = RepeatedPatternFinder(notes, max_length_difference=2)
    rpf.set_similarity_graph()
    m1 = Melody(0, 0)
    m2 = Melody(6, 2)
    assert m2 in rpf._similarity_graph[m1]
    m2 = Melody(6, 3)
    assert m2 not in rpf._similarity_graph[m1]


def test_get_best_melody(rpf):
    best_melody = rpf.get_best_melody()
    assert best_melody.length == 4
    assert best_melody.index == 0


def test_melody_score():
    current_file_dir = Path(__file__).resolve().parent
    file_path = current_file_dir.parent / 'test_pieces' / 'SWV_378.musicxml'

    score = converter.parse(file_path)

    melody = detect_melody(score, max_length_difference=0, max_length=8)
    assert melody.length > 0
