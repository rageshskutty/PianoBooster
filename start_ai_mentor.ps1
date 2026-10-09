# PianoBooster Offline AI Mentor PowerShell Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting PianoBooster Offline AI Mentor Service" -ForegroundColor Green
Write-Host " Target LLM: Local Ollama (qwen2.5-coder:1.5b)" -ForegroundColor Yellow
Write-Host " REST Bridge: http://127.0.0.1:8765" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

python "$PSScriptRoot\ai_mentor\server.py"
