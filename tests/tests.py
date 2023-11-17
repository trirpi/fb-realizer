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
    assert len(s.pitchNamesInChord) == 1
    assert tuple(s.pitchNamesInChord[0]) == ('D', 'G', 'B')
