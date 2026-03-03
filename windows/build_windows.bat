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
if not exist "..\.venv" (
    echo Creating virtual environment...
    python -m venv ..\.venv
)

REM Activate virtual environment
echo Activating virtual environment...
call ..\.venv\Scripts\activate.bat

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
echo Looking in: %CD%\..\models\
echo.

REM Check if cli directory exists
if not exist "..\cli" (
    echo ================================================================
    echo ERROR: 'cli' directory not found!
    echo.
    echo Current directory: %CD%
    echo.
    echo This script must be run from the windows\ subdirectory of the
    echo PokemonDetector project. Make sure you have the complete project structure.
    echo.
    echo Expected structure:
    echo   PokemonDetector\
    echo   ├── cli\
    echo   │   └── main.py
    echo   ├── lib\
    echo   │   └── detector_core.py
    echo   ├── models\
    echo   │   ├── class_names.json
    echo   │   └── best_model_fold1.pth
    echo   └── windows\
    echo       └── build_windows.bat  (this file)
    echo ================================================================
    echo.
    pause
    exit /b 1
)

echo ..\cli directory found
echo Contents of ..\cli:
dir /b ..\cli
echo.

REM Check for required files
if not exist "..\cli\main.py" (
    echo WARNING: main.py not found in ..\cli
)

if not exist "..\models\class_names.json" (
    echo WARNING: class_names.json not found in ..\models
)

REM Check for model file
if not exist "..\models\best_model_fold1.pth" (
    echo.
    echo ================================================================
    echo ERROR: Model file not found!
    echo.
    echo Expected location: %CD%\..\models\best_model_fold1.pth
    echo.
    echo Please download the model from:
    echo https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
    echo.
    echo Save it as: models\best_model_fold1.pth
    echo.
    echo IMPORTANT: Make sure the filename is exactly:
    echo   best_model_fold1.pth
    echo.
    echo NOT:
    echo   best_model_fold1.pth.txt
    echo   best_model_fold1 (1).pth
    echo   best_model_fold1.PTH
    echo ================================================================
    echo.
    pause
    exit /b 1
)

echo [OK] Model file found: best_model_fold1.pth
echo.

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
echo dist\poke.exe ..\gengar.png
echo.
pause
