import logging
import sys
from pathlib import Path

from music21 import converter
from music21.improvedFiguredBass import realizer

if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    logging.log(logging.INFO, 'Started realizing.')
    file_path = Path.cwd() / "test_pieces/Erhore_mich_wenn_ich_rufe_Schutz.musicxml"
    parts = converter.parse(file_path).parts
    basso_continuo = parts[-1]

    # basso_continuo.beatAndMeasureFromOffset()
    # basso_continuo.flatten().getElementsByOffset(4).notes[0]
    fbLine2 = realizer.figuredBassFromStream(basso_continuo)
    fbRealization2 = fbLine2.realize()
    # realized = fbRealization2.generateRandomRealization()
    realized = fbRealization2.generate_optimal_realization()

    stream = parts.stream()
    for part in realized.parts:
        stream.append(part)
    stream.show()
