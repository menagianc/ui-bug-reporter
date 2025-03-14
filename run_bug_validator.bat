@echo off
echo Starting Bug Validator...
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" main.py
pause 