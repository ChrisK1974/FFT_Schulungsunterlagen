@echo off
REM Baut Strukturanlegen.exe lokal (Python 3.8+ muss installiert sein)
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller || goto fehler
python -m PyInstaller --onefile --windowed --clean --name Strukturanlegen Strukturanlegen.py || goto fehler
copy /Y "%~dp0Ordnerstruktur.txt" "%~dp0dist\Ordnerstruktur.txt" >nul || goto fehler
echo.
echo Fertig: %~dp0dist\Strukturanlegen.exe
echo Die Ordnerstruktur liegt daneben: %~dp0dist\Ordnerstruktur.txt
pause
exit /b 0
:fehler
echo Build fehlgeschlagen.
pause
exit /b 1
