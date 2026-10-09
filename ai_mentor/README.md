# PianoBooster Offline AI Mentor System

This module associates **PianoBooster** with an intelligent offline AI Mentor (**Maestro**) that scripts lessons, analyzes real-time MIDI performance telemetry, and dynamically generates adaptive practice drills.

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------------------------+
|                                    PianoBooster (C++ / Qt)                              |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  | CConductor / CSong / CRating Engine                                               |  |
|  |   - Captures micro-timing (lead/lag jitter in ms, early/late)                     |  |
|  |   - Tracks pitch errors, wrong notes, and missed chords per measure               |  |
|  |   - Packages MidiSessionTelemetry payload upon pause / piece completion           |  |
|  +-----------------------------------------------------------------------------------+  |
|                                          ▲                                              |
|                                          │ (Telemetry out / Directives in)              |
|                                          ▼                                              |
|  +-----------------------------------------------------------------------------------+  |
|  | AiMentorBridge (Qt C++)                                                           |  |
|  |   - HTTP REST client communicating with http://127.0.0.1:8765                     |  |
|  |   - Auto-spawns background Python mentor daemon if not running                    |  |
|  |   - Executes remote directives: song loading, tempo, hand, play mode, loop bars   |  |
|  +-----------------------------------------------------------------------------------+  |
|                                          ▲                                              |
|                                          │                                              |
|  +-----------------------------------------------------------------------------------+  |
|  | GuiAiMentorPanel (Qt GUI Dock Widget)                                             |  |
|  |   - Viewable via 'View -> Show AI Mentor Panel' (Ctrl+M) or right dock area       |  |
|  |   - Live mentor status badge (🟢 Online [Ollama Qwen2.5] / 🟡 Rule Fallback)     |  |
|  |   - Rich HTML coaching cards (theory, fingering technique, performance diagnosis) |  |
|  |   - One-click 'Apply Lesson Setup' & 'Adaptive Remedial Drill' buttons            |  |
|  |   - 'Ask Maestro' interactive chat input                                          |  |
|  +-----------------------------------------------------------------------------------+  |
+------------------------------------------┬----------------------------------------------+
                                           │ HTTP / JSON REST API (localhost:8765)
                                           ▼
+-----------------------------------------------------------------------------------------+
|                               Offline AI Mentor Service (Python)                         |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  | HTTP REST Bridge (server.py)                                                      |  |
|  |   - Endpoints: /api/status, /api/curriculum, /api/lesson/current,                 |  |
|  |                /api/evaluate, /api/ask, /api/generate_drill                       |  |
|  +-----------------------------------------------------------------------------------+  |
|                                          ▲                                              |
|                                          ▼                                              |
|  +-----------------------------------------------------------------------------------+  |
|  | Dual-Tier Offline AI Engine (llm_client.py & pedagogy.py)                         |  |
|  |   - Tier 1: Local Ollama (qwen2.5-coder:1.5b on http://localhost:11434)          |  |
|  |             Produces warm, natural, conservatory-grade coaching reflections       |  |
|  |   - Tier 2: Mathematical Music Pedagogy Rules Engine                              |  |
|  |             Evaluates accuracy %, rhythm drift (rushing/dragging), & error bars   |  |
|  |             Guarantees 100% offline uptime even if Ollama is paused/restarting    |  |
|  +-----------------------------------------------------------------------------------+  |
|                                          ▲                                              |
|                                          ▼                                              |
|  +-----------------------------------------------------------------------------------+  |
|  | Curriculum & Procedural Generator (curriculum.py & midi_generator.py)             |  |
|  |   - 10 structured progressive lessons mapped to PianoBooster MIDI library         |  |
|  |   - 4-phase pedagogical progression per piece (Listen -> Tap -> Follow -> Play)  |  |
|  |   - Procedural Standard MIDI Format 0 generator for targeted practice drills      |  |
|  +-----------------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start

### 1. Start the Offline AI Mentor Service
Run either:
```powershell
.\start_ai_mentor.ps1
```
or
```cmd
start_ai_mentor.bat
```
The server will start on `http://127.0.0.1:8765` and automatically detect your local Ollama daemon (`qwen2.5-coder:1.5b`).

### 2. Launch PianoBooster
1. Open PianoBooster.
2. The **AI Piano Mentor** dock panel will appear on the right side of the window (toggle with `Ctrl+M` or via the **View** menu).
3. The mentor badge will confirm: `🟢 AI Mentor: Online (qwen2.5-coder:1.5b)`.
4. Select a lesson from the dropdown and click **▶ Apply Lesson Setup**.
5. Play on your MIDI keyboard. When the piece completes or you pause, Maestro will analyze your performance and script the next drill!

---

## 📖 Scripted Curriculum & Phases

Each lesson contains a 4-phase pedagogical progression:

| Phase | Mode | Goal |
|---|---|---|
| **Phase 1: Active Listening** | `listen` | Internalize the pulse, pitch, and musical phrasing. |
| **Phase 2: Rhythm Tapping** | `rhythmTapping` | Tap the rhythm on any key to develop internal timing without pitch anxiety. |
| **Phase 3: Note Discovery** | `followYou` | PianoBooster pauses until you strike the correct key with proper fingering. |
| **Phase 4: Performance** | `playAlong` | Perform at full tempo alongside the accompaniment with steady rhythm. |

### Syllabus:
1. **Lesson 1**: Finding Middle C & Right Hand Thumb (`01-StartWithMiddleC.mid`)
2. **Lesson 2**: The C Major Triad (`02-ChordOfCMajor.mid`)
3. **Lesson 3**: 5-Finger Pattern (Up and Down) (`03-UpAndDown.mid`)
4. **Lesson 4**: First Classic Melody - Clair de Lune (`04-ClairDeLaLune.mid`)
5. **Lesson 5**: Left Hand Bass - F Major Triad (`05-ChordOfFMajor.mid`)
6. **Lesson 6**: Two-Hand Coordination (`06-DownAndUp.mid`)
7. **Lesson 7**: Lavender's Blue (`02-LavendersBlue.mid`)
8. **Lesson 8**: Frère Jacques (`04-FrereJacques.mid`)
9. **Lesson 9**: Scarborough Fair (`05-ScarboroughFair.mid`)
10. **Lesson 10**: Greensleeves (`06-Greensleeves.mid`)

---

## 🔬 Adaptive Remedial Drill Engine

When a student struggles with a piece:
1. **Spatial Error Localization**: Identifies which measures had errors (e.g., Measures 3 & 4).
2. **Timing Tendency Analysis**:
   - Negative offset (`avg_offset_ms < -35ms`): Student is **rushing** ahead of the beat.
   - Positive offset (`avg_offset_ms > +45ms`): Student is **dragging** behind the beat.
3. **Adaptive Prescription**:
   - Loops only the problem measures (`loop_from` to `loop_to`).
   - Reduces tempo to 75%.
   - Switches to `rhythmTapping` or `followYou` mode depending on whether the error was rhythmic or note-based.
4. **Procedural MIDI Generator**:
   - Dynamically synthesizes custom 5-finger scale exercises and cadence drills on the fly.

---

## 🧪 Testing

Run the automated test suite:
```powershell
python -m unittest ai_mentor\test_ai_mentor.py
```
All tests validate curriculum management, pedagogy diagnostics, procedural MIDI writing, and REST API endpoints.
