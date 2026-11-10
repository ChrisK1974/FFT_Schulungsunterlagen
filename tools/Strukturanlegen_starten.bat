@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 goto use_py

where python >nul 2>nul
if not errorlevel 1 goto use_python
goto python_missing

:use_py
py -3 --version >nul 2>nul
if errorlevel 1 goto use_python
py -3 "%~dp0Strukturanlegen.py"
exit /b %errorlevel%

:use_python
python --version >nul 2>nul
if errorlevel 1 goto python_missing
python "%~dp0Strukturanlegen.py"
exit /b %errorlevel%

:python_missing
echo Python 3 wurde nicht gefunden.
echo Bitte Python 3 installieren und den Python-Launcher oder Python zum PATH hinzufuegen.
echo Download: https://www.python.org/downloads/
pause
exit /b 1
