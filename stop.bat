@echo off
title Stopping PeakCut Services...
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
