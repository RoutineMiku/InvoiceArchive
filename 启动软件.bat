@echo off
REM ============================================================
REM  Invoice Archive - run from source
REM  Requires: Python 3.10+ installed on this computer
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

"%PYEXE%" -c "import PySide6, openpyxl, pdfplumber" >nul 2>nul
if errorlevel 1 (
    echo First run: installing dependencies, please wait...
    "%PYEXE%" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

start "InvoiceArchive" "%PYEXE%" main.py
endlocal
