"""
pedagogy.py - Musical Pedagogy & MIDI Telemetry Diagnostic Engine.
Performs deterministic, rule-based musical performance evaluation on incoming
MIDI telemetry, analyzing rhythm, pitch, finger dexterity, and error patterns.
"""

from typing import Dict, Any, List, Tuple


class PedagogyReport:
    def __init__(
        self,
        passed: bool,
        accuracy: float,
        grade: str,
        timing_diagnosis: str,
        pitch_diagnosis: str,
        coaching_summary: str,
        problem_bars: List[int],
        rushing: bool,
        dragging: bool,
        recommended_action: str,  # "advance_lesson", "advance_phase", "repeat_song", "remedial_drill"
        action_reason: str,
    ):
        self.passed = passed
        self.accuracy = accuracy
        self.grade = grade
        self.timing_diagnosis = timing_diagnosis
        self.pitch_diagnosis = pitch_diagnosis
        self.coaching_summary = coaching_summary
        self.problem_bars = problem_bars
        self.rushing = rushing
        self.dragging = dragging
        self.recommended_action = recommended_action
        self.action_reason = action_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "accuracy": round(self.accuracy, 1),
            "grade": self.grade,
            "timing_diagnosis": self.timing_diagnosis,
            "pitch_diagnosis": self.pitch_diagnosis,
            "coaching_summary": self.coaching_summary,
            "problem_bars": self.problem_bars,
            "rushing": self.rushing,
            "dragging": self.dragging,
            "recommended_action": self.recommended_action,
            "action_reason": self.action_reason,
        }


class PedagogyEngine:
    """Analyzes raw MIDI session telemetry and produces pedagogical diagnosis."""

    @staticmethod
    def analyze_session(
        telemetry: Dict[str, Any],
        lesson_criteria: Dict[str, Any],
        current_phase_idx: int = 2,
    ) -> PedagogyReport:
        total_notes = int(telemetry.get("total_notes", 0))
        wrong_notes = int(telemetry.get("wrong_notes", 0))
        late_notes = int(telemetry.get("late_notes", 0))
        accuracy = float(telemetry.get("accuracy", 0.0))
        problem_bars = telemetry.get("problem_bars", [])
        avg_offset_ms = float(telemetry.get("avg_offset_ms", 0.0))
        timing_jitter_ms = float(telemetry.get("timing_jitter_ms", 0.0))
        notes_history = telemetry.get("notes_history", [])

        # If problem_bars is empty but notes_history has bars, extract them
        if not problem_bars and notes_history:
            bar_counts = {}
            for n in notes_history:
                if n.get("result") in ["wrong", "late"]:
                    b = n.get("bar", 0)
                    if b > 0:
                        bar_counts[b] = bar_counts.get(b, 0) + 1
            # Problem bars are those with more than 1 mistake
            problem_bars = sorted(list(bar_counts.keys()))

        # Timing analysis:
        # Negative offset = playing early (rushing); Positive offset = playing late (dragging)
        rushing = avg_offset_ms < -35.0
        dragging = avg_offset_ms > 45.0

        if rushing:
            timing_diag = f"You are rushing ahead of the metronome pulse by approx {abs(int(avg_offset_ms))} ms. Maintain steady breath and let the beat arrive before pressing the key."
        elif dragging:
            timing_diag = f"You are dragging slightly behind the tempo by approx {int(avg_offset_ms)} ms. Look ahead at the next note in the score before your finger strikes."
        elif timing_jitter_ms > 70.0:
            timing_diag = "Your timing fluctuates between beats. Practice counting subdivisions aloud (1-and-2-and)."
        else:
            timing_diag = "Superb rhythmic precision! Your timing is centered tightly in the groove."

        # Pitch diagnosis
        if wrong_notes == 0 and late_notes == 0:
            pitch_diag = "Flawless pitch accuracy! Every target note and chord was struck cleanly."
        elif wrong_notes == 0 and late_notes > 0:
            pitch_diag = f"No wrong notes, but you hesitated on {late_notes} note(s). Work on anticipating hand movement."
        elif wrong_notes > 0 and problem_bars:
            bars_str = ", ".join(f"Bar {b}" for b in problem_bars[:4])
            pitch_diag = f"Noticed {wrong_notes} slip(s), particularly clustered around {bars_str}. Let's isolate this passage."
        else:
            pitch_diag = f"Registered {wrong_notes} incorrect key strikes and {late_notes} late note(s)."

        # Grade calculation
        if accuracy >= 95.0 and wrong_notes <= 1:
            grade = "A+ (Mastery)"
        elif accuracy >= 90.0 and wrong_notes <= 2:
            grade = "A (Excellent)"
        elif accuracy >= 82.0:
            grade = "B (Good)"
        elif accuracy >= 70.0:
            grade = "C (Developing)"
        else:
            grade = "Needs Reinforcement"

        min_accuracy = float(lesson_criteria.get("min_accuracy", 85.0))
        max_wrong_allowed = int(lesson_criteria.get("max_wrong_notes", 3))

        passed = (accuracy >= min_accuracy) and (wrong_notes <= max_wrong_allowed)

        # Pedagogical Action Decision Matrix
        if passed:
            if current_phase_idx < 3:
                recommended_action = "advance_phase"
                action_reason = (
                    f"Passed phase with {accuracy:.1f}% accuracy! Ready for the next phase."
                )
            else:
                recommended_action = "advance_lesson"
                action_reason = f"Mastered piece with {accuracy:.1f}% accuracy! Ready to graduate to next lesson."
            coaching_summary = (
                f"Bravo! You demonstrated strong control with {accuracy:.1f}% accuracy."
            )
        else:
            if len(problem_bars) > 0 and wrong_notes >= 3:
                recommended_action = "remedial_drill"
                action_reason = (
                    f"Repeated errors clustered in measures {problem_bars}. Looping problem bars."
                )
                coaching_summary = "Good effort! Let's pause and polish the specific problem measures with an isolated drill."
            elif rushing or dragging:
                recommended_action = "remedial_drill"
                action_reason = "Rhythm pulse needs calibration."
                coaching_summary = "Your notes are coming together, but the internal tempo is shifting. Let's do a rhythm drill."
            else:
                recommended_action = "repeat_song"
                action_reason = f"Accuracy ({accuracy:.1f}%) just shy of {min_accuracy}%. One more full attempt will solidify muscle memory."
                coaching_summary = f"Almost there! Try one more pass with relaxed wrists, aiming for {min_accuracy}%."

        return PedagogyReport(
            passed=passed,
            accuracy=accuracy,
            grade=grade,
            timing_diagnosis=timing_diag,
            pitch_diagnosis=pitch_diag,
            coaching_summary=coaching_summary,
            problem_bars=problem_bars,
            rushing=rushing,
            dragging=dragging,
            recommended_action=recommended_action,
            action_reason=action_reason,
        )
