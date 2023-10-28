import argparse
import logging
import sys
import faulthandler
from pathlib import Path

from music21 import converter
from music21.dynamics import Dynamic
from music21.improvedFiguredBass import realizer
from music21.improvedFiguredBass.notation import Modifier
from music21.improvedFiguredBass.rules import RuleSet, RulesConfig
from music21.note import GeneralNote
from music21.stream import Stream, Score, Part
from config import pieces, default_piece

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


def add_dynamic_markings(segments, melody_parts, prev_dynamic=None):
    """Fills in the segments dynamic attribute."""
    if prev_dynamic is None:
        prev_dynamic = 'mf'

    parts = [part.getElementsByClass(Dynamic) for part in melody_parts]
    idxs = [0] * len(melody_parts)
    for segment in segments:
        start_offset = segment.play_offsets[0]
        for i, elts in enumerate(parts):
            while idxs[i] < len(elts) and elts[idxs[i]].offset < start_offset:
                idxs[i] += 1
            if not (idxs[i] < len(elts) and elts[idxs[i]].offset == start_offset):
                if idxs[i] == 0:
                    continue
                idxs[i] -= 1
            prev_dynamic = elts[idxs[i]].value
        segment.dynamic = prev_dynamic

    last_dynamic = prev_dynamic
    last_offset = segments[-1].play_offsets[0]
    for i, elts in enumerate(parts):
        if len(elts) == 0:
            continue
        if elts[-1].offset > last_offset:
            last_dynamic = elts[-1].value
            last_offset = elts[-1].offset
    return last_dynamic


def split_on_rests(bc, melodies):
    result = []

    current_melodies = melodies
    current = bc
    rests = []
    start_offset = 0
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
            prev_start_offset = start_offset
            start_offset = rest_end
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

            result.append((prev, prev_mels, prev_start_offset))
        else:
            result.append((current, current_melodies, start_offset))
            current = None

    return result, rests


def prepare(bass, melody_parts, previous_dynamic_marking, rule_set, start_offset=0):
    logging.log(logging.INFO, 'Parse stream to figured bass.')
    fbLine = realizer.figuredBassFromStream(bass)
    fbRealization = fbLine.realize(rule_set=rule_set, start_offset=start_offset)

    logging.log(logging.INFO, 'Parse melody notes.')
    add_melody_notes(fbRealization._segmentList, melody_parts)

    logging.log(logging.INFO, 'Parse dynamic markings.')
    last_dynamic = add_dynamic_markings(fbRealization._segmentList, melody_parts, previous_dynamic_marking)

    logging.log(logging.INFO, 'Initialize all segments.')
    past_measure = {}
    for segment in fbRealization._segmentList:
        segment.set_pitch_names_in_chord()
        print(segment.fbScale.modify)
        print(segment.notation_string)
        for key, modifier in segment.fbScale.modify.items():
            if (
                key in past_measure and
                    (
                        (past_measure[key].accidental.name == 'flat' and modifier.accidental.name == 'sharp') or
                        (past_measure[key].accidental.name == 'sharp' and modifier.accidental.name == 'flat')
                    )
            ):
                past_measure[key] = Modifier('natural')
            else:
                past_measure[key] = modifier
        print(past_measure)
        segment.update_pitch_names_in_chord(past_measure)

    for segment in fbRealization._segmentList:
        segment.finish_initialization()

    return fbRealization, last_dynamic


def gen_opt(a):
    return a.generate_optimal_realization()


if __name__ == '__main__':
    faulthandler.enable()
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--piece", choices=pieces, default=default_piece)
    args = parser.parse_args()
    piece_name = args.piece
    piece_file_name = pieces[piece_name]["path"]
    piece_signatures = pieces[piece_name]["time_signatures"]

    logging.log(logging.INFO, f'Started realizing {piece_name}')
    file_path = Path.cwd() / "test_pieces" / piece_file_name
    parts = converter.parse(file_path).parts
    basso_continuo_part = parts[-1]
    basso_continuo = basso_continuo_part.flatten().notesAndRests

    # split fbLine on rests
    melody_parts = [p.flatten() for p in parts[:-1]]
    tups, rests = split_on_rests(basso_continuo, melody_parts)

    rule_set = RuleSet(RulesConfig())

    full_harmonies = Stream()
    prev_dynamic = None
    fbRealizations = []
    for i, (bass, melodies, start_offset) in enumerate(tups):
        assert len(bass) > 0
        fbRealization, prev_dynamic = prepare(bass, melodies, prev_dynamic, rule_set, start_offset)
        fbRealizations.append(fbRealization)

    realizations = []
    for fbRealization in fbRealizations:
        realizations.append(fbRealization.generate_optimal_realization())
    # with Pool(5) as p:
    #     realizations = list(p.map(gen_opt, fbRealizations))

    for i, (bass, _, _) in enumerate(tups):
        realization = realizations[i]
        if i > 0:
            full_harmonies.append(rests[i - 1])
        new_harmonies, new_bass = (p.flatten() for p in realization.parts)
        for note in new_harmonies.notes:
            full_harmonies.append(note)

    for time_signature in piece_signatures:
        full_harmonies.insert(time_signature)

    s = Score(id='mainScore')
    harmonies = Part(id='part0')
    for measure in full_harmonies.makeMeasures(refStreamOrTimeRange=parts[0]):
        harmonies.append(measure)
    for part in parts[:-1]: s.insert(0, part)
    s.insert(0, harmonies)
    s.insert(0, parts[-1])
    s.show()
