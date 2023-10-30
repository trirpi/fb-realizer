from music21.meter import TimeSignature

default_piece = "test_maat"

pieces = {
    "ErhoreMich": {"path": "Erhore_mic_wenn_ich_rufe_Schutz.musicxml", "time_signatures": []},
    "OboeConcerto": {"path": "test_pieces/Oboe_Concerto_in_D_minor_Op9_No2__Tomaso_Albinoni.musicxml", "time_signatures": [TimeSignature("2/4")]},
    "SWV_378": {"path": "SWV_378_easy.mxl", "time_signatures": [
        TimeSignature("3/2", offset=11*4),
        TimeSignature("4/4", offset=11*4 + 3*6),
        TimeSignature("3/2", offset=11*4 + 3*6 + 16*4),
        TimeSignature("4/4", offset=11*4 + 3*6 + 16*4 + 12*6),
    ]},
    "test_tussennoot": {"path": "test_tussennoot.musicxml", "time_signatures": []},
    "test_maat": {"path": "test_maat.musicxml", "time_signatures": [
        TimeSignature("3/4", offset=2*4),
        TimeSignature("4/4", offset=2*4 + 3*3),
    ]},
    "test_ignore_accidental": {"path": "test_ignore_accidental.musicxml", "time_signatures": []},
    "test_te_laag": {"path": "test_te_laag.musicxml", "time_signatures": []},
    "test_inversions": {"path": "test_inversions.musicxml", "time_signatures": []},
    "test_accidentals": {"path": "test_accidentals.mxl", "time_signatures": []},
}
