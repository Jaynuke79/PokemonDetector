@echo off
REM Build script for creating Windows executable
REM This script should be run on a Windows machine with Python and dependencies installed

echo ===================================
echo Pokemon Detector Windows Build
echo ===================================
echo.

REM Change to script directory to ensure correct relative paths
cd /d "%~dp0"

REM Show current directory for debugging
echo Current directory: %CD%
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip
pip install pyinstaller
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install timm click numpy pillow

REM Check if model file exists with better diagnostics
echo.
echo Checking for model file...
echo Looking in: %CD%\scripts\cli\
echo.

if exist "scripts\cli\" (
    echo scripts\cli\ directory exists
    echo Contents of scripts\cli\:
    dir /b scripts\cli\
    echo.
) else (
    echo ERROR: scripts\cli\ directory not found!
    echo Make sure you're running this script from the project root directory.
    pause
    exit /b 1
)

if not exist "scripts\cli\best_model_fold1.pth" (
    echo.
    echo ================================================================
    echo WARNING: Model file not found!
    echo.
    echo Expected location: %CD%\scripts\cli\best_model_fold1.pth
    echo.
    echo Please download from:
    echo https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
    echo.
    echo Save the file as: scripts\cli\best_model_fold1.pth
    echo ================================================================
    echo.
    pause
    exit /b 1
) else (
    echo Model file found: scripts\cli\best_model_fold1.pth
    echo.
)

REM Build the executable
echo.
echo Building executable...
pyinstaller --clean poke.spec

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ===================================
echo Build completed successfully!
echo Executable location: dist\poke.exe
echo ===================================
echo.
echo To test the executable, run:
echo dist\poke.exe scripts\cli\gengar.png
echo.
pause
