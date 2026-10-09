"""
curriculum.py - Scripted Curriculum & Adaptive Lesson Engine for PianoBooster.
Provides a structured progression from beginner to intermediate, plus dynamic
remedial drill generation based on student MIDI feedback.
"""

import os
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_COURSES = os.path.join(WORKSPACE_ROOT, "doc", "courses")
BEGINNER_DIR = os.path.join(DOC_COURSES, "BeginnerCourse")
BOOSTER_DIR = os.path.join(DOC_COURSES, "BoosterMusic")


class Lesson:
    def __init__(
        self,
        lesson_id: str,
        title: str,
        subtitle: str,
        level: str,
        midi_file: str,
        theory_notes: str,
        fingering_tips: str,
        hand: str = "right",
        default_speed: float = 0.8,
        min_accuracy: float = 85.0,
        max_wrong_notes: int = 3,
        total_bars: int = 8,
    ):
        self.lesson_id = lesson_id
        self.title = title
        self.subtitle = subtitle
        self.level = level
        self.midi_file = midi_file
        self.theory_notes = theory_notes
        self.fingering_tips = fingering_tips
        self.hand = hand
        self.default_speed = default_speed
        self.min_accuracy = min_accuracy
        self.max_wrong_notes = max_wrong_notes
        self.total_bars = total_bars

        # Standard 4-phase pedagogical progression for each piece
        self.phases = [
            {
                "phase_index": 0,
                "name": "Phase 1: Active Listening",
                "goal": "Listen to the melody and internalize the pulse, pitch, and phrasing.",
                "play_mode": "listen",
                "speed": round(default_speed * 0.9, 2),
                "hand": hand,
                "loop_from": 0.0,
                "loop_to": 0.0,
            },
            {
                "phase_index": 1,
                "name": "Phase 2: Rhythm Tapping",
                "goal": "Tap the rhythm on any key to develop internal timing without pitch anxiety.",
                "play_mode": "rhythmTapping",
                "speed": default_speed,
                "hand": hand,
                "loop_from": 0.0,
                "loop_to": 0.0,
            },
            {
                "phase_index": 2,
                "name": "Phase 3: Note Discovery (Follow You)",
                "goal": "Play the exact notes. PianoBooster pauses until you strike the correct key.",
                "play_mode": "followYou",
                "speed": default_speed,
                "hand": hand,
                "loop_from": 0.0,
                "loop_to": 0.0,
            },
            {
                "phase_index": 3,
                "name": "Phase 4: Performance (Play Along)",
                "goal": "Perform at full tempo alongside the accompaniment with steady rhythm.",
                "play_mode": "playAlong",
                "speed": 1.0,
                "hand": hand,
                "loop_from": 0.0,
                "loop_to": 0.0,
            },
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.lesson_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "level": self.level,
            "midi_file": self.midi_file,
            "theory_notes": self.theory_notes,
            "fingering_tips": self.fingering_tips,
            "hand": self.hand,
            "default_speed": self.default_speed,
            "min_accuracy": self.min_accuracy,
            "max_wrong_notes": self.max_wrong_notes,
            "total_bars": self.total_bars,
            "phases": self.phases,
        }


class CurriculumManager:
    """Manages lesson curriculum, student progression, and adaptive scripting."""

    def __init__(self):
        self.lessons: List[Lesson] = []
        self._load_standard_curriculum()
        self.current_lesson_idx = 0
        self.current_phase_idx = 2  # Default to Phase 3 (Follow You) for interactive play

    def _resolve_midi_path(self, subdir: str, filename: str) -> str:
        candidates = [
            os.path.join(DOC_COURSES, subdir, filename),
            os.path.join(WORKSPACE_ROOT, "music", "BoosterMusicBooks4", subdir, filename),
            os.path.join(WORKSPACE_ROOT, "music", filename),
        ]
        for p in candidates:
            if os.path.exists(p):
                return os.path.abspath(p)
        return os.path.abspath(candidates[0])

    def _load_standard_curriculum(self):
        c1 = self._resolve_midi_path("BeginnerCourse", "01-StartWithMiddleC.mid")
        c2 = self._resolve_midi_path("BeginnerCourse", "02-ChordOfCMajor.mid")
        c3 = self._resolve_midi_path("BeginnerCourse", "03-UpAndDown.mid")
        c4 = self._resolve_midi_path("BeginnerCourse", "04-ClairDeLaLune.mid")
        c5 = self._resolve_midi_path("BeginnerCourse", "05-ChordOfFMajor.mid")
        c6 = self._resolve_midi_path("BeginnerCourse", "06-DownAndUp.mid")

        b1 = self._resolve_midi_path("BoosterMusic", "02-LavendersBlue.mid")
        b2 = self._resolve_midi_path("BoosterMusic", "04-FrereJacques.mid")
        b3 = self._resolve_midi_path("BoosterMusic", "05-ScarboroughFair.mid")
        b4 = self._resolve_midi_path("BoosterMusic", "06-Greensleeves.mid")

        self.lessons = [
            Lesson(
                lesson_id="lesson_01",
                title="Lesson 1: Finding Middle C & Right Hand Thumb",
                subtitle="The anchor note of the piano keyboard and treble/bass clefs.",
                level="Beginner 1",
                midi_file=c1,
                theory_notes="Middle C sits at the center of your 88-key piano keyboard (MIDI note 60). In sheet music, it sits on a ledger line right between the Treble and Bass staves.",
                fingering_tips="Place your Right Hand Thumb (Finger 1) softly curved on Middle C. Keep your wrist level and relaxed.",
                hand="right",
                default_speed=0.75,
                min_accuracy=85.0,
                max_wrong_notes=2,
                total_bars=4,
            ),
            Lesson(
                lesson_id="lesson_02",
                title="Lesson 2: The C Major Triad (C - E - G)",
                subtitle="Forming your very first 3-note piano chord.",
                level="Beginner 1",
                midi_file=c2,
                theory_notes="A triad is formed by stacking notes separated by thirds: C (Root), E (Major Third), and G (Fifth). Striking all three together produces a bright, happy major harmonic sonority.",
                fingering_tips="Use Finger 1 (Thumb) on C, Finger 3 (Middle) on E, and Finger 5 (Pinky) on G. Press with even downward weight like dropping a gentle teardrop.",
                hand="right",
                default_speed=0.75,
                min_accuracy=85.0,
                max_wrong_notes=2,
                total_bars=6,
            ),
            Lesson(
                lesson_id="lesson_03",
                title="Lesson 3: 5-Finger Pattern (Up and Down)",
                subtitle="Developing independent finger dexterity across C - D - E - F - G.",
                level="Beginner 2",
                midi_file=c3,
                theory_notes="This 5-finger pattern is the foundation of modern piano technique. Each finger rests assigned to one white key: 1-C, 2-D, 3-E, 4-F, 5-G.",
                fingering_tips="Keep your fingers naturally curved as if holding a tennis ball. Avoid collapsing your 4th (ring) finger joint.",
                hand="right",
                default_speed=0.8,
                min_accuracy=85.0,
                max_wrong_notes=3,
                total_bars=8,
            ),
            Lesson(
                lesson_id="lesson_04",
                title="Lesson 4: Your First Classic Melody - Clair de Lune",
                subtitle="Playing a lyrical melody using 3 fingers (C, D, E).",
                level="Beginner 2",
                midi_file=c4,
                theory_notes="This gentle French folk tune uses repeated notes and stepwise motion. Listen for smooth legato phrasing (connecting notes smoothly without gaps).",
                fingering_tips="Use 1 on C, 2 on D, and 3 on E. Aim for a singing tone with smooth finger transfers.",
                hand="right",
                default_speed=0.8,
                min_accuracy=88.0,
                max_wrong_notes=2,
                total_bars=8,
            ),
            Lesson(
                lesson_id="lesson_05",
                title="Lesson 5: Left Hand Bass - The F Major Triad",
                subtitle="Introducing the Bass Clef and Left Hand chord shape.",
                level="Beginner 3",
                midi_file=c5,
                theory_notes="The Bass clef (F-clef) handles the lower register. The F Major chord consists of F, A, and C.",
                fingering_tips="Left hand fingering: 5 (Pinky) on low F, 3 (Middle) on A, 1 (Thumb) on Middle C. Notice it has the exact same hand shape as the C Major chord!",
                hand="left",
                default_speed=0.75,
                min_accuracy=85.0,
                max_wrong_notes=2,
                total_bars=6,
            ),
            Lesson(
                lesson_id="lesson_06",
                title="Lesson 6: Two-Hand Coordination - Down and Up",
                subtitle="Synchronizing left hand and right hand patterns.",
                level="Beginner 3",
                midi_file=c6,
                theory_notes="Practicing contrary motion and hand handoff. Playing both hands requires mental spatial separation.",
                fingering_tips="Ensure fingers lift cleanly without lingering on keys from the previous beat.",
                hand="both",
                default_speed=0.75,
                min_accuracy=85.0,
                max_wrong_notes=4,
                total_bars=8,
            ),
            Lesson(
                lesson_id="lesson_07",
                title="Lesson 7: Lavender's Blue",
                subtitle="A traditional English nursery song with charming 3/4 waltz rhythm.",
                level="Intermediate 1",
                midi_file=b1,
                theory_notes="Notice the 3/4 time signature: ONE-two-three, ONE-two-three. Accent beat 1 lightly.",
                fingering_tips="Maintain a buoyant wrist bounce to feel the dance pulse without stiffening.",
                hand="right",
                default_speed=0.8,
                min_accuracy=88.0,
                max_wrong_notes=3,
                total_bars=12,
            ),
            Lesson(
                lesson_id="lesson_08",
                title="Lesson 8: Frère Jacques (Round & Canon)",
                subtitle="Four distinct melodic motifs building rhythmic independence.",
                level="Intermediate 1",
                midi_file=b2,
                theory_notes="Frère Jacques is a canon in 4/4 time. It contains scalewise climbs, leaps, and faster 8th notes.",
                fingering_tips="Keep steady sixteenth/eighth note subdivisions in your head: 1-and-2-and-3-and-4-and.",
                hand="both",
                default_speed=0.85,
                min_accuracy=88.0,
                max_wrong_notes=4,
                total_bars=16,
            ),
            Lesson(
                lesson_id="lesson_09",
                title="Lesson 9: Scarborough Fair",
                subtitle="Dorian mode folk ballad with expressive intervals.",
                level="Intermediate 2",
                midi_file=b3,
                theory_notes="Written in the ancient Dorian folk mode (minor with a natural 6th degree). Expressive and haunting.",
                fingering_tips="Play with deep keybed sensation for expressive cantabile (singing) touch.",
                hand="both",
                default_speed=0.8,
                min_accuracy=85.0,
                max_wrong_notes=5,
                total_bars=24,
            ),
            Lesson(
                lesson_id="lesson_10",
                title="Lesson 10: Greensleeves",
                subtitle="Renaissance masterpiece featuring compound 6/8 meter.",
                level="Intermediate 2",
                midi_file=b4,
                theory_notes="6/8 meter has two strong dotted-quarter pulses per measure: ONE-two-three, FOUR-five-six.",
                fingering_tips="Shape the dynamic arch: crescendo toward the peak note of each phrase, then gentle decrescendo.",
                hand="both",
                default_speed=0.8,
                min_accuracy=85.0,
                max_wrong_notes=5,
                total_bars=32,
            ),
        ]

    def get_current_lesson(self) -> Lesson:
        if 0 <= self.current_lesson_idx < len(self.lessons):
            return self.lessons[self.current_lesson_idx]
        return self.lessons[0]

    def set_current_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]:
        for i, l in enumerate(self.lessons):
            if l.lesson_id == lesson_id:
                self.current_lesson_idx = i
                self.current_phase_idx = 2  # Default to follow-you
                return l
        return None

    def next_lesson(self) -> Lesson:
        if self.current_lesson_idx + 1 < len(self.lessons):
            self.current_lesson_idx += 1
            self.current_phase_idx = 2
        return self.get_current_lesson()

    def previous_lesson(self) -> Lesson:
        if self.current_lesson_idx > 0:
            self.current_lesson_idx -= 1
            self.current_phase_idx = 2
        return self.get_current_lesson()

    def set_phase(self, phase_idx: int) -> Dict[str, Any]:
        lesson = self.get_current_lesson()
        if 0 <= phase_idx < len(lesson.phases):
            self.current_phase_idx = phase_idx
        return self.get_active_directives()

    def get_active_directives(self) -> Dict[str, Any]:
        """Builds directives sent to PianoBooster to configure playback."""
        lesson = self.get_current_lesson()
        phase = lesson.phases[min(self.current_phase_idx, len(lesson.phases) - 1)]

        return {
            "action": "configure_lesson",
            "lesson_id": lesson.lesson_id,
            "lesson_title": lesson.title,
            "phase_name": phase["name"],
            "phase_index": self.current_phase_idx,
            "song_path": lesson.midi_file,
            "speed": phase["speed"],
            "play_mode": phase["play_mode"],
            "hand": phase["hand"],
            "loop_from": phase["loop_from"],
            "loop_to": phase["loop_to"],
            "auto_play": False,
        }

    def script_adaptive_remedial_drill(
        self,
        problem_bars: List[int],
        rushing: bool,
        dragging: bool,
        accuracy: float,
    ) -> Dict[str, Any]:
        """
        Dynamically scripts a remedial drill when student encounters difficulties.
        Isolates problem bars, lowers tempo, and selects optimal practice mode.
        """
        lesson = self.get_current_lesson()

        if problem_bars:
            start_bar = max(1, min(problem_bars) - 1)
            end_bar = min(lesson.total_bars, max(problem_bars) + 1)
        else:
            start_bar = 1
            end_bar = min(lesson.total_bars, 4)

        # Adaptive tempo reduction
        reduced_speed = max(0.5, round(lesson.default_speed * 0.75, 2))

        # Select mode based on nature of mistake
        if rushing or dragging:
            recommended_mode = "rhythmTapping"
            mode_rationale = (
                "Rhythm instability detected. We will use Rhythm Tapping mode to lock into the beat."
            )
        elif accuracy < 70.0:
            recommended_mode = "followYou"
            mode_rationale = (
                "Pitch accuracy below threshold. PianoBooster will wait for your finger on each key."
            )
        else:
            recommended_mode = "playAlong"
            mode_rationale = "Focused loop practice at 75% tempo."

        directives = {
            "action": "remedial_drill",
            "lesson_id": lesson.lesson_id,
            "drill_title": f"Targeted Isolation Drill: Measures {start_bar} to {end_bar}",
            "rationale": mode_rationale,
            "song_path": lesson.midi_file,
            "speed": reduced_speed,
            "play_mode": recommended_mode,
            "hand": lesson.hand,
            "loop_from": float(start_bar),
            "loop_to": float(end_bar),
            "auto_play": False,
        }
        return directives
