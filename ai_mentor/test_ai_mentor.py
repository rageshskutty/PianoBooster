"""
test_ai_mentor.py - End-to-end unit and integration tests for PianoBooster AI Mentor.
Tests curriculum loading, pedagogy diagnostics, procedural MIDI generation,
and HTTP REST API endpoints.
"""

import unittest
import os
import json
import threading
import time
import urllib.request

from curriculum import CurriculumManager, Lesson
from pedagogy import PedagogyEngine, PedagogyReport
from llm_client import OfflineMentorLLM
from midi_generator import MidiBuilder, generate_scale_exercise, generate_chord_drill
from server import run_server, DEFAULT_PORT


class TestCurriculum(unittest.TestCase):
    def setUp(self):
        self.mgr = CurriculumManager()

    def test_curriculum_loaded(self):
        self.assertGreaterEqual(len(self.mgr.lessons), 6)
        first_lesson = self.mgr.get_current_lesson()
        self.assertEqual(first_lesson.lesson_id, "lesson_01")
        self.assertIn("Middle C", first_lesson.title)

    def test_lesson_phases(self):
        lesson = self.mgr.get_current_lesson()
        self.assertEqual(len(lesson.phases), 4)
        modes = [p["play_mode"] for p in lesson.phases]
        self.assertEqual(modes, ["listen", "rhythmTapping", "followYou", "playAlong"])

    def test_adaptive_remedial_drill_scripting(self):
        drill = self.mgr.script_adaptive_remedial_drill(
            problem_bars=[3, 4],
            rushing=False,
            dragging=True,
            accuracy=65.0,
        )
        self.assertEqual(drill["action"], "remedial_drill")
        self.assertEqual(drill["play_mode"], "rhythmTapping")  # dragging triggers rhythm tap
        self.assertLessEqual(drill["speed"], 0.75)
        self.assertEqual(drill["loop_from"], 2.0)  # max(1, 3-1)
        self.assertEqual(drill["loop_to"], float(self.mgr.get_current_lesson().total_bars))  # clamped to total bars


class TestPedagogy(unittest.TestCase):
    def test_mastery_session(self):
        telemetry = {
            "total_notes": 40,
            "wrong_notes": 0,
            "late_notes": 0,
            "accuracy": 100.0,
            "avg_offset_ms": 10.0,
            "timing_jitter_ms": 15.0,
            "problem_bars": [],
        }
        criteria = {"min_accuracy": 85.0, "max_wrong_notes": 2}
        report = PedagogyEngine.analyze_session(telemetry, criteria, current_phase_idx=2)
        self.assertTrue(report.passed)
        self.assertIn("Mastery", report.grade)
        self.assertEqual(report.recommended_action, "advance_phase")

    def test_rushing_detection(self):
        telemetry = {
            "total_notes": 35,
            "wrong_notes": 2,
            "late_notes": 1,
            "accuracy": 78.0,
            "avg_offset_ms": -55.0,  # Negative = rushing
            "timing_jitter_ms": 40.0,
            "problem_bars": [2, 3],
        }
        criteria = {"min_accuracy": 85.0, "max_wrong_notes": 2}
        report = PedagogyEngine.analyze_session(telemetry, criteria, current_phase_idx=2)
        self.assertFalse(report.passed)
        self.assertTrue(report.rushing)
        self.assertIn("rushing", report.timing_diagnosis.lower())
        self.assertEqual(report.recommended_action, "remedial_drill")


class TestMidiGenerator(unittest.TestCase):
    def test_scale_generation(self):
        output_file = "test_scale_output.mid"
        try:
            path = generate_scale_exercise(output_file, root_note=60, bpm=90)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100)
            with open(path, "rb") as f:
                header = f.read(4)
                self.assertEqual(header, b"MThd")
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)

    def test_chord_generation(self):
        output_file = "test_chord_output.mid"
        try:
            path = generate_chord_drill(output_file, bpm=80)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100)
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


class TestServerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_port = 8769
        cls.server_thread = threading.Thread(target=run_server, args=(cls.test_port,), daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    def _get(self, path):
        url = f"http://127.0.0.1:{self.test_port}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path, payload):
        url = f"http://127.0.0.1:{self.test_port}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_api_status(self):
        data = self._get("/api/status")
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["mentor_name"], "Maestro")
        self.assertIn("llm", data)

    def test_api_curriculum(self):
        data = self._get("/api/curriculum")
        self.assertGreaterEqual(data["total_lessons"], 6)

    def test_api_lesson_selection(self):
        resp = self._post("/api/lesson/select", {"lesson_id": "lesson_02"})
        self.assertTrue(resp["success"])
        self.assertEqual(resp["lesson"]["id"], "lesson_02")
        self.assertIn("directives", resp)

    def test_api_telemetry_evaluation(self):
        telemetry = {
            "total_notes": 25,
            "wrong_notes": 1,
            "late_notes": 0,
            "accuracy": 96.0,
            "avg_offset_ms": 5.0,
            "timing_jitter_ms": 12.0,
            "problem_bars": [],
        }
        resp = self._post("/api/evaluate", telemetry)
        self.assertTrue(resp["success"])
        self.assertIn("coaching_html", resp)
        self.assertIn("report", resp)
        self.assertTrue(resp["report"]["passed"])

    def test_api_generate_drill(self):
        resp = self._post("/api/generate_drill", {"drill_type": "scale", "root_note": 60, "bpm": 90})
        self.assertTrue(resp["success"])
        self.assertTrue(os.path.exists(resp["midi_path"]))


if __name__ == "__main__":
    unittest.main()
