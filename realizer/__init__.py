import logging

from music21 import note
from music21.figuredBass import realizer as music21_realizer


def realize():
    logging.log(logging.INFO, 'Realized.')
    bass_line = music21_realizer.FiguredBassLine()
    bass_line.addElement(note.Note('C3'))

    bass_line.realize().generateRandomRealization().show()
