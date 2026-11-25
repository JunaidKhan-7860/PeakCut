@echo off
title Khan Clipping - Antigravity 1-Click Installer
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0install_antigravity.ps1"
pause
