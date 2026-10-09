"""
midi_generator.py - Pure Python Procedural MIDI File Generator.
Generates Standard MIDI Files (SMF Format 0) without external dependencies,
used to dynamically generate custom remedial drills and exercises on demand.
"""

import struct
from typing import List, Tuple, Optional


def write_vlq(value: int) -> bytes:
    """Encodes an integer into MIDI variable-length quantity bytes."""
    buf = bytearray()
    buf.append(value & 0x7F)
    value >>= 7
    while value > 0:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    buf.reverse()
    return bytes(buf)


class MidiBuilder:
    """Constructs a single-track MIDI format 0 file."""

    def __init__(self, ticks_per_beat: int = 480, bpm: int = 100):
        self.ticks_per_beat = ticks_per_beat
        self.bpm = bpm
        self.track_data = bytearray()
        self.current_time_ticks = 0

        # Set initial tempo (microseconds per quarter note)
        tempo_us = int(60_000_000 / max(20, bpm))
        self.track_data += b"\x00\xFF\x51\x03" + struct.pack(">I", tempo_us)[1:]

        # Set default 4/4 time signature
        self.track_data += b"\x00\xFF\x58\x04\x04\x02\x18\x08"

    def add_note(
        self,
        note: int,
        duration_beats: float,
        channel: int = 0,
        velocity: int = 80,
        delta_beats: float = 0.0,
    ):
        """Adds a note-on and note-off event sequence."""
        delta_ticks = int(delta_beats * self.ticks_per_beat)
        duration_ticks = int(duration_beats * self.ticks_per_beat)

        # Note On
        self.track_data += write_vlq(delta_ticks)
        self.track_data += bytes([0x90 | (channel & 0x0F), note & 0x7F, velocity & 0x7F])

        # Note Off
        self.track_data += write_vlq(duration_ticks)
        self.track_data += bytes([0x80 | (channel & 0x0F), note & 0x7F, 0])

    def add_chord(
        self,
        notes: List[int],
        duration_beats: float,
        channel: int = 0,
        velocity: int = 80,
        delta_beats: float = 0.0,
    ):
        """Adds simultaneous notes in a chord."""
        if not notes:
            return
        duration_ticks = int(duration_beats * self.ticks_per_beat)
        delta_ticks = int(delta_beats * self.ticks_per_beat)

        # First note has delta_ticks
        self.track_data += write_vlq(delta_ticks)
        self.track_data += bytes([0x90 | (channel & 0x0F), notes[0] & 0x7F, velocity & 0x7F])

        # Subsequent notes have delta 0
        for n in notes[1:]:
            self.track_data += write_vlq(0)
            self.track_data += bytes([0x90 | (channel & 0x0F), n & 0x7F, velocity & 0x7F])

        # Note-off for first note after duration
        self.track_data += write_vlq(duration_ticks)
        self.track_data += bytes([0x80 | (channel & 0x0F), notes[0] & 0x7F, 0])

        # Note-off for remaining notes with delta 0
        for n in notes[1:]:
            self.track_data += write_vlq(0)
            self.track_data += bytes([0x80 | (channel & 0x0F), n & 0x7F, 0])

    def write_file(self, filepath: str):
        """Writes the MIDI file to disk."""
        # Add End of Track event
        self.track_data += b"\x00\xFF\x2F\x00"

        # Build MThd header: Format 0, 1 track, ticks_per_beat
        mthd = struct.pack(">4sIHHH", b"MThd", 6, 0, 1, self.ticks_per_beat)

        # Build MTrk chunk: chunk ID, length, data
        mtrk = struct.pack(">4sI", b"MTrk", len(self.track_data)) + bytes(self.track_data)

        with open(filepath, "wb") as f:
            f.write(mthd)
            f.write(mtrk)


def generate_scale_exercise(filepath: str, root_note: int = 60, bpm: int = 85) -> str:
    """Generates a 5-finger scale practice exercise."""
    builder = MidiBuilder(ticks_per_beat=480, bpm=bpm)
    scale_steps = [0, 2, 4, 5, 7, 5, 4, 2, 0]  # C D E F G F E D C

    # Play twice
    for _ in range(2):
        for step in scale_steps:
            builder.add_note(root_note + step, duration_beats=1.0, delta_beats=0.0)

    builder.write_file(filepath)
    return filepath


def generate_chord_drill(filepath: str, bpm: int = 80) -> str:
    """Generates an alternating triad cadence drill (C -> F -> G -> C)."""
    builder = MidiBuilder(ticks_per_beat=480, bpm=bpm)
    # C Maj (C4 E4 G4), F Maj (C4 F4 A4), G Maj (B3 D4 G4), C Maj (C4 E4 G4)
    chords = [
        [60, 64, 67],  # C
        [60, 65, 69],  # F
        [59, 62, 67],  # G
        [60, 64, 67],  # C
    ]
    for _ in range(2):
        for chord in chords:
            builder.add_chord(chord, duration_beats=2.0, delta_beats=0.0)

    builder.write_file(filepath)
    return filepath
