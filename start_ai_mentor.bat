@echo off
title PianoBooster AI Mentor Service
echo ============================================================
echo   Starting PianoBooster Offline AI Mentor Service
echo   Connecting to local Ollama (qwen2.5-coder:1.5b)
echo   Listening on http://127.0.0.1:8765
echo ============================================================
python "%~dp0ai_mentor\server.py"
pause
