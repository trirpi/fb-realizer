from pathlib import Path

import pytest

from realize import realize_from_path
from config import pieces, default_piece
from music21.improvedFiguredBass.segment import Segment


def test_segment():
    s = Segment('D', '6,4')
    s.set_pitch_names_in_chord()
    s.finish_initialization()
    assert hasattr(s, 'dynamic')
    assert hasattr(s, 'notation_string')
    assert hasattr(s, 'next_segment')
    assert hasattr(s, 'prev_segment')
    assert hasattr(s, 'notation_string')
    assert len(s.pitch_names_in_chord) == 1
    assert tuple(s.pitch_names_in_chord[0]) == ('D', 'G', 'B')


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
