@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::  Rick and Morty - Multiverse Mayhem  (v1.3.0.3)  --  EXE Builder
::  Strictly requires Python 3.13.12
::
::  Put this .bat in the SAME folder as:
::     - Rick and Morty RPG.py          (the game script)
::     - icon.ico                    (window/exe icon)   [optional]
::     - version.txt                    (exe version info)  [optional]
::  Then just double-click it.
:: ============================================================================

:: ---- EDIT THESE IF YOU RENAME FILES --------------------------------------
set "SCRIPT_NAME=Rick and Morty RPG.py"
set "EXE_NAME=Rick and Morty - Multiverse Mayhem"
set "ICON=icon.ico"
set "VERSION_FILE=version.txt"
:: --------------------------------------------------------------------------

set "REQUIRED_VERSION=3.13.12"
set "DOWNLOAD_URL=https://www.python.org/downloads/release/python-31312/"

echo Checking Python version...

:: --- Find an interpreter that is EXACTLY 3.13.12 --------------------------
:: Prefer the "py" launcher pinned to 3.13, then fall back to "python" on PATH.
set "PY_CMD="
set "VER_A="
set "VER_B="

for /f "tokens=2" %%I in ('py -3.13 --version 2^>nul') do set "VER_A=%%I"
if "!VER_A!"=="%REQUIRED_VERSION%" set "PY_CMD=py -3.13"

if not defined PY_CMD (
    for /f "tokens=2" %%I in ('python --version 2^>nul') do set "VER_B=%%I"
    if "!VER_B!"=="%REQUIRED_VERSION%" set "PY_CMD=python"
)

if not defined PY_CMD (
    set "CURRENT_VERSION=!VER_B!"
    if not defined CURRENT_VERSION set "CURRENT_VERSION=!VER_A!"
    if not defined CURRENT_VERSION set "CURRENT_VERSION=None"
    if "!CURRENT_VERSION!"=="" set "CURRENT_VERSION=None"
    goto :WrongVersion
)

echo Python %REQUIRED_VERSION% detected via "!PY_CMD!". Proceeding with setup...
echo =======================================================

:: --- Locate the game script -----------------------------------------------
if not exist "%SCRIPT_NAME%" (
    echo "%SCRIPT_NAME%" not found next to this script. Searching...
    for %%F in ("Rick and Morty RPG.py") do set "SCRIPT_NAME=%%~nxF"
)
if not exist "%SCRIPT_NAME%" (
    echo ERROR: Could not find the game .py file.
    echo Put this .bat next to it, or edit SCRIPT_NAME at the top of this file.
    goto :End
)
echo Using game script: "%SCRIPT_NAME%"

:: 1. Create Virtual Environment
echo [1/6] Creating virtual environment...
%PY_CMD% -m venv .venv
if %ERRORLEVEL% NEQ 0 ( echo ERROR: venv creation failed. & goto :End )

:: 2. Activate Virtual Environment
echo [2/6] Activating virtual environment...
call ".venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: could not activate venv. & goto :End )

:: 3. Upgrade build tools
echo [3/6] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel

:: 4. Install Requirements (this game needs none, but honored if present)
echo [4/6] Installing dependencies from requirements.txt...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo No requirements.txt found - the game uses only the standard library, so that's fine.
)

:: 5. Install PyInstaller
echo [5/6] Installing PyInstaller...
python -m pip install pyinstaller
if %ERRORLEVEL% NEQ 0 ( echo ERROR: PyInstaller install failed. & goto :End )

:: 6. Build the executable
echo [6/6] Building executable...

set "HAVE_ICON=0"
set "HAVE_VER=0"
if exist "%ICON%" set "HAVE_ICON=1"
if exist "%VERSION_FILE%" set "HAVE_VER=1"

if "!HAVE_ICON!!HAVE_VER!"=="11" (
    echo   ...with icon and version info.
    pyinstaller --onefile --windowed --clean --noconfirm --collect-all tkinter --hidden-import=tkinter --add-data "%ICON%;." --icon "%ICON%" --version-file "%VERSION_FILE%" --name "%EXE_NAME%" "%SCRIPT_NAME%"
) else if "!HAVE_ICON!"=="1" (
    echo   WARNING: %VERSION_FILE% missing - building without version metadata.
    pyinstaller --onefile --windowed --clean --noconfirm --collect-all tkinter --hidden-import=tkinter --add-data "%ICON%;." --icon "%ICON%" --name "%EXE_NAME%" "%SCRIPT_NAME%"
) else if "!HAVE_VER!"=="1" (
    echo   WARNING: %ICON% missing - building without a custom icon.
    pyinstaller --onefile --windowed --clean --noconfirm --collect-all tkinter --hidden-import=tkinter --version-file "%VERSION_FILE%" --name "%EXE_NAME%" "%SCRIPT_NAME%"
) else (
    echo   WARNING: %ICON% and %VERSION_FILE% missing - building bare.
    pyinstaller --onefile --windowed --clean --noconfirm --collect-all tkinter --hidden-import=tkinter --name "%EXE_NAME%" "%SCRIPT_NAME%"
)

if %ERRORLEVEL% NEQ 0 (
    echo =======================================================
    echo ERROR: Build failed. Scroll up for the PyInstaller error.
    goto :End
)

echo =======================================================
echo Build completed successfully!
echo Your executable is here:  dist\%EXE_NAME%.exe
goto :End

:WrongVersion
echo =======================================================
echo ERROR: Incorrect Python Version!
echo.
echo You currently have: Python !CURRENT_VERSION!
echo This script requires exactly: Python %REQUIRED_VERSION%
echo.
echo Please download and install Python %REQUIRED_VERSION% from here:
echo %DOWNLOAD_URL%
echo.
echo Make sure to check the box "Add Python to PATH" during installation.
echo =======================================================
start "" "%DOWNLOAD_URL%"

:End
echo Press any key to exit...
pause >nul
exit /b