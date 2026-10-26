@echo off
REM Baut STW_Pruefstruktur.exe lokal (Python 3.8+ muss installiert sein)
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller || goto fehler
python -m PyInstaller --onefile --windowed --clean --name STW_Pruefstruktur stw_pruefstruktur.py || goto fehler
echo.
echo Fertig: %~dp0dist\STW_Pruefstruktur.exe
pause
exit /b 0
:fehler
echo Build fehlgeschlagen.
pause
exit /b 1
