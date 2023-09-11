import logging
import sys
from pathlib import Path

from music21 import converter
from music21.figuredBass import realizer

if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    logging.log(logging.INFO, 'Started realizing.')
    file_path = Path.cwd() / "test_file.musicxml"
    part = converter.parse(file_path).parts[-1]
    fbLine2 = realizer.figuredBassFromStream(part)
    fbRealization2 = fbLine2.realize()
    fbRealization2.generateRandomRealization().show()
