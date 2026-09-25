@echo off
REM Restart local Prompt Studio (stop port listeners, then start foreground).
REM Run from any directory; switches to repo root (parent of scripts\).
cd /d "%~dp0.."
if exist ".\.venv\Scripts\python.exe" (
  ".\.venv\Scripts\python.exe" -m apps.prompt_studio restart %*
) else (
  python -m apps.prompt_studio restart %*
)
