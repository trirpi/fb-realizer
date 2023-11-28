from pathlib import Path

import pytest

from music21.pitch import Pitch
from realize import realize_from_path
from config import pieces, default_piece
from music21.improvedFiguredBass.segment import Segment, SegmentOption
from music21.improvedFiguredBass.possibility import Possibility


@pytest.fixture
def segment() -> Segment:
    s = Segment('D3', '6,4')
    s.set_pitch_names_in_chord()
    s.finish_initialization()
    return s


@pytest.fixture
def segment_option(segment) -> SegmentOption:
    return segment.segment_options[0]


@pytest.fixture
def possibility() -> Possibility:
    return Possibility((Pitch('D3'), Pitch('G3'), Pitch('B3')), 0)


def test_segment(segment):
    assert hasattr(segment, 'dynamic')
    assert hasattr(segment, 'next_segment')
    assert hasattr(segment, 'prev_segment')
    assert len(segment.segment_options) == 1


def test_intermediate_note(segment, possibility):
    intermediate_notes = segment.get_intermediate_notes(possibility)
    assert len(intermediate_notes) == 6
    pitch, voice = intermediate_notes[0]
    assert voice == 0
    assert pitch == Pitch('E3')
    pitch, voice = intermediate_notes[1]
    assert voice == 0
    assert pitch == Pitch('C3')
    pitch, voice = intermediate_notes[5]
    assert voice == 2
    assert pitch == Pitch('A3')


def test_segment_options(segment_option):
    assert tuple(segment_option.pitch_names_in_chord) == ('D', 'G', 'B')





def test_realization():
    piece_name = default_piece
    piece_file_name = pieces[piece_name]['path']

    current_file_dir = Path(__file__).resolve().parent
    file_path = current_file_dir.parent / 'test_pieces' / piece_file_name
    realize_from_path(file_path, start_measure=None, end_measure=None)


@pytest.mark.parametrize("piece_name, args", pieces.items())
def test_realizations(piece_name, args):
    current_file_dir = Path(__file__).resolve().parent
    file_path = current_file_dir.parent / 'test_pieces' / args['path']
    realize_from_path(file_path, start_measure=0, end_measure=2)
