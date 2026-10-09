"""
server.py - PianoBooster Offline AI Mentor HTTP REST Bridge.
Runs locally on http://127.0.0.1:8765, connecting PianoBooster with the offline
AI mentor, curriculum scripts, and Ollama LLM.
"""

import sys
import os
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from curriculum import CurriculumManager
from pedagogy import PedagogyEngine
from llm_client import OfflineMentorLLM
from midi_generator import generate_scale_exercise, generate_chord_drill

DEFAULT_PORT = 8765
GENERATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "generated"))
os.makedirs(GENERATED_DIR, exist_ok=True)


class MentorState:
    def __init__(self):
        self.curriculum = CurriculumManager()
        self.llm = OfflineMentorLLM()
        self.last_telemetry: Dict[str, Any] = {}
        self.last_report: Dict[str, Any] = {}
        self.last_directives: Dict[str, Any] = self.curriculum.get_active_directives()
        self.last_coaching_html: str = ""


STATE = MentorState()


class MentorRequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json_response(self, data: Any, status_code: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        try:
            if path in ["", "/api", "/api/status"]:
                llm_health = STATE.llm.check_health()
                lesson = STATE.curriculum.get_current_lesson()
                self._send_json_response(
                    {
                        "mentor_name": "Maestro",
                        "status": "online",
                        "llm": llm_health,
                        "current_lesson": {
                            "id": lesson.lesson_id,
                            "title": lesson.title,
                            "phase_index": STATE.curriculum.current_phase_idx,
                            "phase_name": lesson.phases[STATE.curriculum.current_phase_idx]["name"],
                        },
                        "last_directives": STATE.last_directives,
                    }
                )
            elif path == "/api/curriculum":
                lessons_data = [l.to_dict() for l in STATE.curriculum.lessons]
                self._send_json_response(
                    {
                        "total_lessons": len(lessons_data),
                        "current_lesson_index": STATE.curriculum.current_lesson_idx,
                        "lessons": lessons_data,
                    }
                )
            elif path == "/api/lesson/current":
                lesson = STATE.curriculum.get_current_lesson()
                directives = STATE.curriculum.get_active_directives()
                self._send_json_response(
                    {
                        "lesson": lesson.to_dict(),
                        "current_phase_idx": STATE.curriculum.current_phase_idx,
                        "directives": directives,
                        "last_coaching_html": STATE.last_coaching_html,
                    }
                )
            else:
                self._send_json_response({"error": "Endpoint not found"}, status_code=404)
        except Exception as e:
            self._send_json_response(
                {"error": str(e), "traceback": traceback.format_exc()}, status_code=500
            )

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

            if path == "/api/lesson/select":
                lesson_id = payload.get("lesson_id", "")
                lesson = STATE.curriculum.set_current_lesson_by_id(lesson_id)
                if lesson:
                    STATE.last_directives = STATE.curriculum.get_active_directives()
                    welcome_text = f"<h3>Welcome to {lesson.title}</h3><p>{lesson.theory_notes}</p><p><strong>Technique Tip:</strong> {lesson.fingering_tips}</p>"
                    STATE.last_coaching_html = welcome_text
                    self._send_json_response(
                        {
                            "success": True,
                            "lesson": lesson.to_dict(),
                            "directives": STATE.last_directives,
                            "coaching_html": welcome_text,
                        }
                    )
                else:
                    self._send_json_response(
                        {"success": False, "error": f"Lesson {lesson_id} not found"},
                        status_code=404,
                    )

            elif path == "/api/lesson/phase":
                phase_idx = int(payload.get("phase_index", 2))
                directives = STATE.curriculum.set_phase(phase_idx)
                STATE.last_directives = directives
                self._send_json_response({"success": True, "directives": directives})

            elif path == "/api/lesson/next":
                lesson = STATE.curriculum.next_lesson()
                directives = STATE.curriculum.get_active_directives()
                STATE.last_directives = directives
                welcome_text = f"<h3>Advancing to {lesson.title}</h3><p>{lesson.theory_notes}</p><p><strong>Technique Tip:</strong> {lesson.fingering_tips}</p>"
                STATE.last_coaching_html = welcome_text
                self._send_json_response(
                    {
                        "success": True,
                        "lesson": lesson.to_dict(),
                        "directives": directives,
                        "coaching_html": welcome_text,
                    }
                )

            elif path == "/api/lesson/previous":
                lesson = STATE.curriculum.previous_lesson()
                directives = STATE.curriculum.get_active_directives()
                STATE.last_directives = directives
                self._send_json_response(
                    {"success": True, "lesson": lesson.to_dict(), "directives": directives}
                )

            elif path in ["/api/telemetry", "/api/evaluate"]:
                # Process incoming MIDI session feedback from PianoBooster
                if payload:
                    STATE.last_telemetry = payload

                lesson = STATE.curriculum.get_current_lesson()
                criteria = {
                    "min_accuracy": lesson.min_accuracy,
                    "max_wrong_notes": lesson.max_wrong_notes,
                }

                report = PedagogyEngine.analyze_session(
                    telemetry=STATE.last_telemetry,
                    lesson_criteria=criteria,
                    current_phase_idx=STATE.curriculum.current_phase_idx,
                )
                STATE.last_report = report.to_dict()

                # Generate mentoring review using local LLM (or fallback)
                lesson_info = {
                    "title": lesson.title,
                    "subtitle": lesson.subtitle,
                    "theory_notes": lesson.theory_notes,
                    "fingering_tips": lesson.fingering_tips,
                    "min_accuracy": lesson.min_accuracy,
                    "phase_name": lesson.phases[STATE.curriculum.current_phase_idx]["name"],
                }

                coaching_feedback = STATE.llm.generate_coaching_feedback(
                    lesson_info=lesson_info,
                    pedagogy_report=STATE.last_report,
                    telemetry=STATE.last_telemetry,
                )
                STATE.last_coaching_html = coaching_feedback

                # Decide on next directives:
                # If passed, advance phase or lesson; if struggling with problem bars, script remedial drill!
                if report.recommended_action == "advance_phase":
                    new_phase = STATE.curriculum.current_phase_idx + 1
                    directives = STATE.curriculum.set_phase(new_phase)
                elif report.recommended_action == "advance_lesson":
                    next_les = STATE.curriculum.next_lesson()
                    directives = STATE.curriculum.get_active_directives()
                elif report.recommended_action == "remedial_drill":
                    directives = STATE.curriculum.script_adaptive_remedial_drill(
                        problem_bars=report.problem_bars,
                        rushing=report.rushing,
                        dragging=report.dragging,
                        accuracy=report.accuracy,
                    )
                else:
                    # Repeat attempt
                    directives = STATE.curriculum.get_active_directives()

                STATE.last_directives = directives

                self._send_json_response(
                    {
                        "success": True,
                        "report": STATE.last_report,
                        "coaching_html": coaching_feedback,
                        "directives": directives,
                    }
                )

            elif path == "/api/ask":
                question = payload.get("question", "").strip()
                if not question:
                    self._send_json_response(
                        {"success": False, "error": "Empty question"}, status_code=400
                    )
                    return

                lesson = STATE.curriculum.get_current_lesson()
                answer = STATE.llm.answer_question(
                    question=question,
                    lesson_info={
                        "title": lesson.title,
                        "theory_notes": lesson.theory_notes,
                        "fingering_tips": lesson.fingering_tips,
                    },
                )
                self._send_json_response({"success": True, "question": question, "answer": answer})

            elif path == "/api/generate_drill":
                drill_type = payload.get("drill_type", "scale")
                root_note = int(payload.get("root_note", 60))
                bpm = int(payload.get("bpm", 85))

                filename = f"drill_{drill_type}_{root_note}_{bpm}.mid"
                filepath = os.path.join(GENERATED_DIR, filename)

                if drill_type == "chord":
                    generate_chord_drill(filepath, bpm=bpm)
                else:
                    generate_scale_exercise(filepath, root_note=root_note, bpm=bpm)

                self._send_json_response(
                    {
                        "success": True,
                        "drill_type": drill_type,
                        "midi_path": filepath,
                        "directives": {
                            "action": "load_generated_drill",
                            "song_path": filepath,
                            "speed": 1.0,
                            "play_mode": "followYou",
                            "hand": "right",
                            "loop_from": 0.0,
                            "loop_to": 0.0,
                        },
                    }
                )
            else:
                self._send_json_response({"error": "Endpoint not found"}, status_code=404)

        except Exception as e:
            self._send_json_response(
                {"error": str(e), "traceback": traceback.format_exc()}, status_code=500
            )

    def log_message(self, format, *args):
        # Concise logging to stdout
        sys.stdout.write(f"[AI Mentor Bridge] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(port: int = DEFAULT_PORT):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, MentorRequestHandler)
    print(f"============================================================")
    print(f" PianoBooster Offline AI Mentor Service")
    print(f" Listening on http://127.0.0.1:{port}")
    print(f" Local LLM Target: {STATE.llm.ollama_url} (Model: {STATE.llm.model})")
    print(f" Loaded {len(STATE.curriculum.lessons)} curriculum lessons")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down AI Mentor service...")
        httpd.server_close()


if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
