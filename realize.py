import argparse
import logging
import sys
from pathlib import Path

from music21 import converter, analysis
from music21.dynamics import Dynamic
from music21.improvedFiguredBass import realizer
from music21.improvedFiguredBass.notation import Modifier
from music21.improvedFiguredBass.realizer import FiguredBassLineException
from music21.improvedFiguredBass.rules import RuleSet
from music21.improvedFiguredBass.segment import Segment
from music21.meter import TimeSignature
from music21.note import GeneralNote
from music21.pitch import Accidental, Pitch
from music21.stream import Stream, Score, Part
from config import pieces, default_piece


def set_melody_notes(segments, melody_parts):
    """Fills in the segments melody_notes attribute."""
    idxs = [0] * len(melody_parts)
    for segment in segments:
        start_offset = segment.play_offsets[0]
        for i, part in enumerate(melody_parts):
            elts = part.notesAndRests
            while idxs[i] < len(elts) and elts[idxs[i]].offset < start_offset:
                idxs[i] += 1
            if not (idxs[i] < len(elts) and elts[idxs[i]].offset == start_offset):
                if idxs[i] == 0:
                    continue
                idxs[i] -= 1
            melody_note: GeneralNote = elts[idxs[i]]
            if melody_note.isNote:
                segment.melody_pitches.add(elts[idxs[i]])


def set_dynamic_markings(segments, melody_parts, prev_dynamic=None):
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
        for i, note in enumerate(current.notesAndRests):
            if note.isRest:
                rest = current.notesAndRests[i]
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


def set_neighboring_segments(segment_list: list[Segment]):
    for i, segment in enumerate(segment_list):
        prev_seg = segment_list[i - 1] if i > 0 else None
        next_seg = segment_list[i + 1] if i < len(segment_list) - 1 else None
        segment.prev_segment = prev_seg
        segment.next_segment = next_seg


def set_on_beat(segment_list, time_signature, start_offset: int):
    for i, segment in enumerate(segment_list):
        offset = segment.play_offsets[0] + start_offset
        segment.on_beat = 0
        segment.on_beat += offset % 1 == 0
        segment.on_beat += offset % time_signature.beatDivisionCount == 0


def handle_accidentals(segment_list):
    MINOR_INTERVALS = {1, 3, 8, 10}
    MAJOR_INTERVALS = {2, 4, 9, 11}

    past_measure = {}
    for i, segment in enumerate(segment_list):
        segment_measure = segment.bassNote.measureNumber or 0
        segment.set_pitch_names_in_chord()
        for note in segment.melody_pitches:
            note_name = note.fullName[:1]
            if 'sharp' in note.fullName:
                past_measure[note_name] = (Modifier('sharp'), segment_measure)
            elif 'flat' in note.fullName:
                past_measure[note_name] = (Modifier('flat'), segment_measure)
            else:
                past_measure[note_name] = (Modifier('natural'), segment_measure)
        for note in list(past_measure.keys()):
            if past_measure[note][1] < segment_measure - 1:
                del past_measure[note]

        for key, modifier in segment.fbScale.modify.items():
            if key in past_measure and past_measure[key][1] < segment_measure - 1:
                del past_measure[key]
            if (
                    key in past_measure and
                    (
                            (past_measure[key][0].accidental.name == 'flat' and modifier.accidental.name == 'sharp') or
                            (past_measure[key][0].accidental.name == 'sharp' and modifier.accidental.name == 'flat')
                    )
            ):
                past_measure[key] = (Modifier('natural'), segment_measure)
            else:
                if modifier.accidental.name == 'sharp' and Pitch(key).ps - segment.bassNote.pitch.ps in MAJOR_INTERVALS:
                    modifier.accidental = Accidental('natural')
                elif modifier.accidental.name == 'flat' and Pitch(
                        key).ps - segment.bassNote.pitch.ps in MINOR_INTERVALS:
                    modifier.accidental = Accidental('natural')
                past_measure[key] = (modifier, segment_measure)
        segment.update_pitch_names_in_chord(past_measure)

    for segment in segment_list:
        segment.finish_initialization()


def prepare(bass, melody_parts, previous_dynamic_marking, rule_set, start_offset, time_signature):
    logging.log(logging.INFO, 'Parse stream to figured bass.')
    fb_line = realizer.figured_bass_from_stream(bass)
    fb_realization = fb_line.realize(rule_set=rule_set, start_offset=start_offset)

    set_neighboring_segments(fb_realization.segment_list)
    set_melody_notes(fb_realization.segment_list, melody_parts)
    last_dynamic = set_dynamic_markings(fb_realization.segment_list, melody_parts, previous_dynamic_marking)
    handle_accidentals(fb_realization.segment_list)
    set_on_beat(fb_realization.segment_list, time_signature, start_offset)

    return fb_realization, last_dynamic


def realize_from_path(path, start_measure, end_measure):
    if start_measure and not end_measure:
        raise FiguredBassLineException("Cannot only input starting measure.")
    logging.log(logging.INFO, f'Started realizing {path}')

    score = converter.parse(path)
    if end_measure:
        start_measure = start_measure or 0
        score = score.measures(start_measure, end_measure)

    parts = score.parts
    basso_continuo_stream = parts[-1]

    realized_part = realize_part(basso_continuo_stream, score)
    return create_score(parts, realized_part)


def set_key(bass_part, score):
    wa = analysis.windowed.WindowedAnalysis(score, analysis.discrete.KrumhanslKessler())
    window_size = 12
    a, b = wa.analyze(windowSize=min(window_size, int(bass_part.highestTime)))
    for note in bass_part.flatten().notes:
        window_left = min(max(0, int(note.offset) - window_size + min(int(note.duration.quarterLength), 4)), len(a)-1)
        note.key_pitch_class = a[window_left][0].ps % 12
        note.key_name = a[window_left][0].name


def realize_part(basso_continuo_part, score):
    basso_continuo = basso_continuo_part.flatten()
    time_signature = basso_continuo.timeSignature

    set_key(basso_continuo, score)

    # split fbLine on rests
    melody_parts = [p.flatten() for p in score.parts[:-1]]
    tups, rests = split_on_rests(basso_continuo, melody_parts)

    rule_set = RuleSet()

    full_harmonies = Stream()
    prev_dynamic = None
    fbRealizations = []
    for i, (bass, melodies, start_offset) in enumerate(tups):
        if bass.quarterLength == 0:
            fbRealizations.append(None)
            continue
        fbRealization, prev_dynamic = prepare(bass, melodies, prev_dynamic, rule_set, start_offset, time_signature)
        fbRealizations.append(fbRealization)

    realizations = []
    for fbRealization in fbRealizations:
        if fbRealization is None:
            realizations.append(None)
            continue
        logging.log(logging.INFO, "Generating Optimal Realization.\n\n")
        realizations.append(fbRealization.generate_optimal_realization())

    for i, (bass, _, _) in enumerate(tups):
        realization = realizations[i]
        if realization is None:
            continue
        if i > 0:
            full_harmonies.append(rests[i - 1])
        new_harmonies, new_bass = (p.flatten() for p in realization.parts)
        for note in new_harmonies.notes:
            full_harmonies.append(note)

    # reconstruct proper formatting
    time_signatures = basso_continuo_part.recurse().getElementsByClass(TimeSignature)
    for time_signature in time_signatures:
        time_signature.offset = time_signature.getOffsetBySite(basso_continuo_part.recurse())
        full_harmonies.insert(time_signature)

    if basso_continuo.keySignature:
        full_harmonies.insert(basso_continuo.keySignature)

    harmonies = Part(id='part0')
    for measure in full_harmonies.makeMeasures(refStreamOrTimeRange=score.parts[0]):
        harmonies.append(measure)

    return harmonies


def create_score(parts, harmonies):
    s = Score(id='mainScore')
    for part in parts[:-1]:
        s.insert(0, part)
    s.insert(0, harmonies)
    s.insert(0, parts[-1])
    return s


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", type=int, help="Measure to start realizing from.", default=None)
    parser.add_argument("-e", "--end", type=int, help="Measure to end realizing.", default=None)
    parser.add_argument("-p", "--piece", choices=pieces, default=default_piece)
    parser.add_argument("-L", "--logging", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO if args.logging else logging.ERROR,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    piece_name = args.piece
    piece_file_name = pieces[piece_name]["path"]

    file_path = Path.cwd() / "test_pieces" / piece_file_name
    realize_from_path(file_path, start_measure=args.start, end_measure=args.end).show()
