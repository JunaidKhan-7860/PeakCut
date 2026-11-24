@echo off
title Starting PeakCut AI Studio...
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0launch.ps1"
pause
