from pathlib import Path

import pytest

from realize import realize_from_path
from config import pieces, default_piece
from music21.improvedFiguredBass.segment import Segment, SegmentOption


def test_segment():
    s = Segment('D', '6,4')
    s.set_pitch_names_in_chord()
    s.finish_initialization()
    assert hasattr(s, 'dynamic')
    assert hasattr(s, 'next_segment')
    assert hasattr(s, 'prev_segment')
    assert len(s.segment_options) == 1


def test_segment_options():
    s = Segment('D', '6,4')
    s.set_pitch_names_in_chord()
    s.finish_initialization()
    segment_option: SegmentOption = s.segment_options[0]
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
