import logging
import sys
from pathlib import Path

from music21 import converter
from music21.improvedFiguredBass import realizer
from music21.note import Note

if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    logging.log(logging.INFO, 'Started realizing.')
    file_path = Path.cwd() / "test_pieces/test_file.musicxml"
    parts = converter.parse(file_path).parts
    basso_continuo = parts[-1]

    fbLine = realizer.figuredBassFromStream(basso_continuo)
    fbRealization = fbLine.realize()

    melody_parts = [p.flatten() for p in parts[:-1]]
    current_idx = [0 for _ in melody_parts]
    for segment in fbRealization._segmentList:
        start_offset = segment.play_offsets[0]
        for i, part in enumerate(melody_parts):
            while current_idx[i] < len(part.notes) and part.notes[current_idx[i]].offset < start_offset:
                current_idx[i] += 1
            if not (current_idx[i] < len(part.notes) and part.notes[current_idx[i]].offset == start_offset):
                if current_idx[i] == 0: continue
                current_idx[i] -= 1
            melody_note: Note = part.notes[current_idx[i]]
            if not melody_note.isRest:
                segment.melody_notes.add(part.notes[current_idx[i]])

    # realized = fbRealization2.generateRandomRealization()
    realized = fbRealization.generate_optimal_realization()

    stream = parts.stream()
    for part in realized.parts:
        stream.append(part)
    stream.show()
