import logging
import sys
from pathlib import Path

from music21 import converter
from music21.dynamics import Dynamic
from music21.improvedFiguredBass import realizer
from music21.note import GeneralNote


def add_melody_notes(segments, melody_parts):
    """Fills in the segments melody_notes attribute."""
    idxs = [0] * len(melody_parts)
    for segment in segments:
        start_offset = segment.play_offsets[0]
        for i, part in enumerate(melody_parts):
            elts = part.notesAndRests
            while idxs[i] < len(elts) and elts[idxs[i]].offset < start_offset:
                idxs[i] += 1
            if not (idxs[i] < len(elts) and elts[idxs[i]].offset == start_offset):
                if idxs[i] == 0: continue
                idxs[i] -= 1
            melody_note: GeneralNote = elts[idxs[i]]
            if melody_note.isNote:
                segment.melody_notes.add(elts[idxs[i]])


def add_dynamic_markings(segments, melody_parts):
    """Fills in the segments dynamic attribute."""
    parts = [part.getElementsByClass(Dynamic) for part in melody_parts]
    idxs = [0] * len(melody_parts)
    for segment in segments:
        start_offset = segment.play_offsets[0]
        for i, elts in enumerate(parts):
            while idxs[i] < len(elts) and elts[idxs[i]].offset < start_offset:
                idxs[i] += 1
            if not (idxs[i] < len(elts) and elts[idxs[i]].offset == start_offset):
                if idxs[i] == 0: continue
                idxs[i] -= 1
            segment.dynamic = elts[idxs[i]].value


def split_on_rests(bc, melodies):
    result = []

    current_melodies = melodies
    current = bc
    rests = []
    while current:
        rest = None
        for note in list(current):
            if note.isRest:
                rest = note
                break
        if rest:
            rests.append(rest)
            rest_start = rest.offset
            rest_length = rest.quarterLength
            rest_end = rest_start + rest_length
            prev, current = current.splitAtQuarterLength(rest_start)
            _, current = current.splitAtQuarterLength(rest_length)
            current = current.notesAndRests
            prev_mels = []
            new_mels = []
            for mel in current_melodies:
                prev_mel, curr_mel = mel.splitAtQuarterLength(rest_end)
                prev_mels.append(prev_mel)
                new_mels.append(curr_mel)
            current_melodies = new_mels

            result.append((prev, prev_mels))
        else:
            result.append((current, current_melodies))
            current = None

    return result, rests


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    logging.log(logging.INFO, 'Started realizing.')
    # file_path = Path.cwd() / "test_pieces/Erhore_mich_wenn_ich_rufe_Schutz4.musicxml"
    file_path = Path.cwd() / "test_pieces/Oboe_Concerto_in_D_minor_Op9_No2__Tomaso_Albinoni.musicxml"
    # file_path = Path.cwd() / "test_pieces/test_file.musicxml"
    parts = converter.parse(file_path).parts
    basso_continuo = parts[-1].flatten().notesAndRests

    # split fbLine on rests
    melody_parts = [p.flatten() for p in parts[:-1]]
    tups, rests = split_on_rests(basso_continuo, melody_parts)

    logging.log(logging.INFO, 'Parse stream to figured bass.')
    fbLine = realizer.figuredBassFromStream(basso_continuo)
    fbRealization = fbLine.realize()

    logging.log(logging.INFO, 'Parse melody notes.')
    add_melody_notes(fbRealization._segmentList, melody_parts)

    logging.log(logging.INFO, 'Parse dynamic markings.')
    add_dynamic_markings(fbRealization._segmentList, melody_parts)

    logging.log(logging.INFO, 'Generating optimal realization.')
    realized = fbRealization.generate_optimal_realization()

    stream = parts.stream()
    for part in realized.parts:
        stream.append(part)
    stream.show()
