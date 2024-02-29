from pathlib import Path
import random
from timeit import default_timer

import pytest
from matplotlib import pyplot as plt, rc

import realize
from music21 import converter
from music21.pitch import Pitch
from realize import realize_from_path
from config import pieces, default_piece
from music21.improvedFiguredBass.segment import Segment, SegmentOption
from music21.improvedFiguredBass.possibility import Possibility


def get_realization(file_name):
    current_file_dir = Path(__file__).resolve().parent
    file_path = current_file_dir.parent / 'test_pieces' / file_name

    score = converter.parse(file_path)
    bc_part = score.parts[-1]
    melody_parts = score.parts[:-1]

    realization, _ = realize.prepare(bc_part, melody_parts)
    return realization


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
    intermediate_notes = list(segment.get_intermediate_int_pitches(possibility, possibility))
    assert len(intermediate_notes) == 7
    pitch, voice = intermediate_notes[0]
    assert voice == 0
    assert pitch == Pitch('E3').ps
    pitch, voice = intermediate_notes[2]
    assert voice == 0
    assert pitch == Pitch('C3').ps
    pitch, voice = intermediate_notes[5]
    assert voice == 1
    assert pitch == Pitch('F3').ps


def test_segment_options(segment_option):
    assert tuple(segment_option.pitch_names_in_chord) == ('D', 'G', 'B')


def test_melody_notes_at_strike(segment):
    realization = get_realization('test_melody_notes.musicxml')

    melody_pitches_first = list(realization.segment_list[0].melody_pitches_at_strike)
    assert len(melody_pitches_first) == 1
    assert melody_pitches_first[0] == Pitch("E4")

    melody_pitches_second = list(realization.segment_list[1].melody_pitches_at_strike)
    assert len(melody_pitches_second) == 1
    assert melody_pitches_second[0] == Pitch("A4")


def test_melody_notes(segment):
    realization = get_realization('test_melody_notes.musicxml')
    melody_pitches_first = realization.segment_list[0].melody_pitches
    assert len(melody_pitches_first) == 4
    assert Pitch("E4") in melody_pitches_first
    assert Pitch("F4") in melody_pitches_first
    assert Pitch("G4") in melody_pitches_first
    assert Pitch("A4") in melody_pitches_first
    melody_pitches_second = realization.segment_list[1].melody_pitches
    assert len(melody_pitches_second) == 3
    assert Pitch("A4") in melody_pitches_second
    assert Pitch("C5") in melody_pitches_second
    assert Pitch("E5") in melody_pitches_second


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


@pytest.mark.skip("Visual test")
def test_realization_speed():
    plt.rcdefaults()
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "font.size": 14,
    })

    current_file_dir = Path(__file__).resolve().parent
    file_path = current_file_dir.parent / 'test_pieces' / 'Erhore_mich_wenn_ich_rufe_Schutz.musicxml'

    x = []
    y = []
    for i in range(20):
        random_num_measures = random.randint(15, 40)
        random_start_measure = random.randint(0, 60-random_num_measures)
        end_measure = random_start_measure + random_num_measures

        start = default_timer()
        _, num_b, num_m = realize_from_path(file_path, start_measure=random_start_measure, end_measure=end_measure)
        # num_b = random.randint(5, 10)
        end = default_timer()

        x.append(num_b)
        y.append(end - start)
    plt.scatter(x, y)
    plt.xlabel("Number of bass notes")
    plt.ylabel("Execution time (s)")
    plt.savefig("bass_notes_execution_time.eps", format="eps", dpi=1200, bbox_inches="tight", transparent=True)
    plt.show()
    print("done")
