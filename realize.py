import logging
import sys
from pathlib import Path

from music21 import converter
from music21.dynamics import Dynamic
from music21.improvedFiguredBass import realizer
from music21.meter import TimeSignature
from music21.note import GeneralNote
from music21.stream import Stream, Score, Part


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
        for i, note in enumerate(current):
            if note.isRest:
                rest = current[i]
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
                dynamics = prev_mel.getElementsByClass(Dynamic)
                if len(dynamics) > 0 and dynamics[-1].offset == rest_end:
                    curr_mel.insert(0, dynamics[-1])
                prev_mels.append(prev_mel)
                new_mels.append(curr_mel)
            current_melodies = new_mels

            result.append((prev, prev_mels))
        else:
            result.append((current, current_melodies))
            current = None

    return result, rests


def create_figured_bass(bass, melody_parts):
    logging.log(logging.INFO, 'Parse stream to figured bass.')
    fbLine = realizer.figuredBassFromStream(bass)
    fbRealization = fbLine.realize()

    logging.log(logging.INFO, 'Parse melody notes.')
    add_melody_notes(fbRealization._segmentList, melody_parts)

    logging.log(logging.INFO, 'Parse dynamic markings.')
    add_dynamic_markings(fbRealization._segmentList, melody_parts)

    logging.log(logging.INFO, 'Generating optimal realization.')
    realized = fbRealization.generate_optimal_realization()

    return realized


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    logging.log(logging.INFO, 'Started realizing.')
    # file_path = Path.cwd() / "test_pieces/Erhore_mich_wenn_ich_rufe_Schutz.musicxml"
    file_path = Path.cwd() / "test_pieces/Oboe_Concerto_in_D_minor_Op9_No2__Tomaso_Albinoni.musicxml"
    parts = converter.parse(file_path).parts
    basso_continuo_part = parts[-1]
    basso_continuo = basso_continuo_part.flatten().notesAndRests

    # split fbLine on rests
    melody_parts = [p.flatten() for p in parts[:-1]]
    tups, rests = split_on_rests(basso_continuo, melody_parts)

    full_bass = Stream()
    full_bass.append(TimeSignature('2/4'))
    full_harmonies = Stream()
    full_harmonies.append(TimeSignature('2/4'))
    for i, (bass, melodies) in enumerate(tups):
        if i > 0:
            full_bass.append(rests[i - 1])
            full_harmonies.append(rests[i - 1])
        if len(bass) == 0:
            continue
        realization = create_figured_bass(bass, melodies)
        new_harmonies, new_bass = (p.flatten() for p in realization.parts)
        for note in new_harmonies.notes:
            full_harmonies.append(note)
        for note in new_bass.notes:
            full_bass.append(note)

    s = Score(id='mainScore')
    harmonies = Part(id='part0')
    bass = Part(id='part1')
    for measure in full_harmonies.makeMeasures(refStreamOrTimeRange=parts[0]):
        harmonies.append(measure)
    for measure in full_bass.makeMeasures(refStreamOrTimeRange=parts[0]):
        bass.append(measure)
    for part in parts: s.insert(0, part)
    s.insert(0, harmonies)
    s.insert(0, bass)
    s.show()
    # full_bass.show()
    # stream = parts.stream()
    # stream.append(full_harmonies)
    # stream.append(full_bass)
    # stream.show()
