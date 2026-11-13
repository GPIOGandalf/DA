@echo off
cd /d "%~dp0"
python tdot_demo.py
if errorlevel 1 pause
