"""
llm_client.py - Offline LLM Interface for PianoBooster AI Mentor.
Communicates with local Ollama instance (e.g. qwen2.5-coder:1.5b) to generate
natural, personalized piano teacher coaching, with seamless offline rule-based fallback.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

OLLAMA_DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:1.5b"

MAESTRO_SYSTEM_PROMPT = """You are Maestro, an empathetic, discerning, and inspiring piano mentor inside PianoBooster.
Your job is to mentor a student learning the piano. You examine their real-time MIDI performance data:
- Note Accuracy (%)
- Wrong Notes count
- Late / Hesitation Notes count
- Timing offset in milliseconds (negative = rushing ahead of beat, positive = dragging behind beat)
- Problem measures / bars

GUIDELINES:
1. Speak with warmth, encouragement, and deep musical wisdom (like a dedicated conservatory instructor).
2. Highlight one strong positive aspect first.
3. Offer concrete, physical piano technique advice (e.g., wrist height, curving fingers, counting subdivisions like '1-and-2-and', anticipating chord shapes).
4. Address their specific mistakes without overwhelming them.
5. Keep your response concise (3 short paragraphs maximum) so it is easy to read while sitting at the piano keyboard.
"""


class OfflineMentorLLM:
    """Handles communication with local Ollama server, with instant fallback."""

    def __init__(self, ollama_url: str = OLLAMA_DEFAULT_URL, model: str = DEFAULT_MODEL):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.last_status = "untested"

    def check_health(self) -> Dict[str, Any]:
        """Checks if local Ollama daemon is reachable and lists models."""
        url = f"{self.ollama_url}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PianoBooster-AIMentor/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    self.last_status = "online"
                    return {
                        "online": True,
                        "url": self.ollama_url,
                        "active_model": self.model,
                        "available_models": models,
                    }
        except Exception as e:
            self.last_status = f"offline ({str(e)})"

        return {
            "online": False,
            "url": self.ollama_url,
            "active_model": self.model,
            "available_models": [],
            "note": "Using built-in deterministic pedagogical rules engine.",
        }

    def generate_coaching_feedback(
        self,
        lesson_info: Dict[str, Any],
        pedagogy_report: Dict[str, Any],
        telemetry: Dict[str, Any],
    ) -> str:
        """
        Generates natural teacher coaching using Ollama, falling back to rule templates.
        """
        # First check if Ollama is responsive
        prompt = f"""Student Performance Report:
Lesson: {lesson_info.get('title')} ({lesson_info.get('subtitle', '')})
Current Phase: {lesson_info.get('phase_name', 'Interactive Practice')}
Target Accuracy Threshold: {lesson_info.get('min_accuracy', 85)}%
Actual Accuracy: {pedagogy_report.get('accuracy', 0)}%
Grade: {pedagogy_report.get('grade', 'N/A')}
Passed: {pedagogy_report.get('passed', False)}

MIDI Feedback Metrics:
- Total Notes: {telemetry.get('total_notes', 0)}
- Wrong Notes: {telemetry.get('wrong_notes', 0)}
- Late / Hesitation Notes: {telemetry.get('late_notes', 0)}
- Average Timing Deviation: {telemetry.get('avg_offset_ms', 0)} ms
- Rushing: {pedagogy_report.get('rushing', False)}
- Dragging: {pedagogy_report.get('dragging', False)}
- Problem Measures: {pedagogy_report.get('problem_bars', [])}
- Primary Diagnostic: {pedagogy_report.get('timing_diagnosis', '')}
- Pitch Diagnostic: {pedagogy_report.get('pitch_diagnosis', '')}
- Next Action: {pedagogy_report.get('action_reason', '')}

Please write a concise 3-paragraph mentor review addressing the student directly. Focus on physical piano mechanics, musical feel, and what to focus on next."""

        llm_response = self._call_ollama(prompt)
        if llm_response:
            return llm_response

        # Fallback to rich, high-quality rule-based coaching
        return self._generate_fallback_coaching(lesson_info, pedagogy_report, telemetry)

    def answer_question(self, question: str, lesson_info: Dict[str, Any]) -> str:
        """Answers a student question about piano technique or theory."""
        prompt = f"""The student is currently working on:
Lesson: {lesson_info.get('title')}
Theory: {lesson_info.get('theory_notes')}
Fingering: {lesson_info.get('fingering_tips')}

The student asks: "{question}"

Provide a clear, helpful, and concise answer from the perspective of Maestro, their piano teacher."""

        resp = self._call_ollama(prompt)
        if resp:
            return resp

        # Fallback response
        return f"Regarding '{question}': Focus on keeping your wrists relaxed and level with the keyboard. In this lesson ({lesson_info.get('title')}), remember the core principle: {lesson_info.get('fingering_tips')}. Break difficult transitions into small 2-note fragments and practice them slowly."

    def _call_ollama(self, prompt: str) -> Optional[str]:
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": MAESTRO_SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 200,
            },
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("response", "").strip()
                    if text:
                        return text
        except Exception:
            pass
        return None

    def _generate_fallback_coaching(
        self,
        lesson_info: Dict[str, Any],
        pedagogy_report: Dict[str, Any],
        telemetry: Dict[str, Any],
    ) -> str:
        passed = pedagogy_report.get("passed", False)
        accuracy = pedagogy_report.get("accuracy", 0.0)
        grade = pedagogy_report.get("grade", "B")
        problem_bars = pedagogy_report.get("problem_bars", [])
        timing_diag = pedagogy_report.get("timing_diagnosis", "")
        pitch_diag = pedagogy_report.get("pitch_diagnosis", "")

        if passed:
            p1 = f"Well done on completing this run of <strong>{lesson_info.get('title')}</strong>! You achieved an accuracy of <strong>{accuracy:.1f}%</strong> (Grade: {grade}). Your key strikes showed confidence and growing familiarity with the score."
            p2 = f"<em>Rhythm & Tone:</em> {timing_diag} {pitch_diag}"
            p3 = f"<strong>Next Step:</strong> {pedagogy_report.get('action_reason', 'Ready to advance!')} Remember to keep your wrists buoyant and shoulders relaxed as we proceed."
        else:
            p1 = f"Good effort on <strong>{lesson_info.get('title')}</strong>! You achieved <strong>{accuracy:.1f}%</strong> accuracy (Grade: {grade}). Every run trains your neural pathways and builds muscle memory."
            p2 = f"<em>Analysis:</em> {timing_diag} {pitch_diag}"
            if problem_bars:
                bars_txt = ", ".join(f"Bar {b}" for b in problem_bars[:3])
                p3 = f"<strong>Prescription:</strong> Let's isolate {bars_txt}. {pedagogy_report.get('action_reason', '')} Take a deep breath, drop your weight into the keys, and let's try again!"
            else:
                p3 = f"<strong>Prescription:</strong> {pedagogy_report.get('action_reason', 'Try one more run!')} Focus on looking ahead at the next measure before striking."

        return f"<p>{p1}</p><p>{p2}</p><p>{p3}</p>"
