import logging
import sys
from pathlib import Path

from music21 import converter
from music21.dynamics import Dynamic
from music21.improvedFiguredBass import realizer
from music21.note import GeneralNote

if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    logging.log(logging.INFO, 'Started realizing.')
    file_path = Path.cwd() / "test_pieces/Erhore_mich_wenn_ich_rufe_Schutz4.musicxml"
    # file_path = Path.cwd() / "test_pieces/Oboe_Concerto_in_D_minor_Op9_No2__Tomaso_Albinoni.musicxml"
    # file_path = Path.cwd() / "test_pieces/test_file.musicxml"
    parts = converter.parse(file_path).parts
    basso_continuo = parts[-1]

    # split fbLine on rests
    # split melody pieces on rests as well?

    logging.log(logging.INFO, 'Parse stream to figured bass.')
    fbLine = realizer.figuredBassFromStream(basso_continuo)
    fbRealization = fbLine.realize()

    logging.log(logging.INFO, 'Parse melody notes.')
    melody_parts = [p.flatten() for p in parts[:-1]]
    current_idx = [0 for _ in melody_parts]
    for segment in fbRealization._segmentList:
        start_offset = segment.play_offsets[0]
        for i, part in enumerate(melody_parts):
            elts = part.notesAndRests
            while current_idx[i] < len(elts) and elts[current_idx[i]].offset < start_offset:
                current_idx[i] += 1
            if not (current_idx[i] < len(elts) and elts[current_idx[i]].offset == start_offset):
                if current_idx[i] == 0: continue
                current_idx[i] -= 1
            melody_note: GeneralNote = elts[current_idx[i]]
            if melody_note.isNote:
                segment.melody_notes.add(elts[current_idx[i]])

    logging.log(logging.INFO, 'Parse dynamic markings.')
    dynamic_idx = 0
    dynamic_elts = melody_parts[0].getElementsByClass(Dynamic)
    for segment in fbRealization._segmentList:
        segment.dynamic = 'mf'
        start_offset = segment.play_offsets[0]
        while dynamic_idx < len(dynamic_elts) and dynamic_elts[dynamic_idx].offset < start_offset:
            dynamic_idx += 1
        if not (dynamic_idx < len(dynamic_elts) and dynamic_elts[dynamic_idx].offset == start_offset):
            if dynamic_idx == 0: continue
            dynamic_idx -= 1
        segment.dynamic = dynamic_elts[dynamic_idx].value

    logging.log(logging.INFO, 'Generating optimal realization.')
    # realized = fbRealization2.generateRandomRealization()
    realized = fbRealization.generate_optimal_realization()

    stream = parts.stream()
    for part in realized.parts:
        stream.append(part)
    stream.show()
