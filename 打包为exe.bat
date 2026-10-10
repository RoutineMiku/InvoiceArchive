@echo off
REM ============================================================
REM  Build a standalone Windows exe with PyInstaller
REM  Output: dist\InvoiceArchive\InvoiceArchive.exe
REM ============================================================
setlocal
cd /d "%~dp0"

set "PYEXE="
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYEXE for /f "delims=" %%i in ('where python 2^>nul') do if not defined PYEXE set "PYEXE=%%i"

if not defined PYEXE (
    echo [ERROR] Python 3 not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

"%PYEXE%" -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

"%PYEXE%" -m PyInstaller --noconfirm --clean --onedir --windowed --name InvoiceArchive ^
  --icon app.ico ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebChannel ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtPdf ^
  --exclude-module reportlab ^
  --exclude-module pymupdf ^
  --exclude-module fitz ^
  --exclude-module tkinter ^
  --exclude-module matplotlib ^
  --exclude-module numpy ^
  --exclude-module pandas ^
  main.py

echo.
echo Done. Output folder: %~dp0dist\InvoiceArchive
explorer "%~dp0dist\InvoiceArchive"
pause
endlocal
