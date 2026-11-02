@echo off
REM Build script for the Windows executables and, if Inno Setup is installed, the installer
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

REM .venv can belong to Linux when the repo is shared with WSL, so Windows keeps its own
if not exist "..\.venv-win" (
    echo Creating virtual environment...
    python -m venv ..\.venv-win
)

REM Activate virtual environment
echo Activating virtual environment...
call ..\.venv-win\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.7.1+cpu torchvision==0.22.1+cpu
python -m pip install -r ..\requirements.txt pyinstaller
if %errorlevel% neq 0 (
    echo.
    echo Installing dependencies failed!
    pause
    exit /b %errorlevel%
)

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

REM Build the executables
echo.
echo Building executables...
python -m PyInstaller --noconfirm --clean poke.spec

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ===================================
echo Build completed successfully!
echo CLI: dist\PokemonDetector\poke.exe
echo Web app: dist\PokemonDetector\PokemonDetector.exe
echo ===================================
echo.
echo To test the CLI, run:
echo dist\PokemonDetector\poke.exe ..\gengar.png
echo.

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo To build the installer, install Inno Setup 6 from https://jrsoftware.org/isinfo.php
    echo and run this script again.
    echo.
    pause
    exit /b 0
)

echo Compiling the installer...
for /f "usebackq delims=" %%V in (`python -c "import tomllib; print(tomllib.load(open('../pyproject.toml', 'rb'))['project']['version'])"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION (
    echo Could not read the version from pyproject.toml. This step needs Python 3.11 or newer.
    pause
    exit /b 1
)
"%ISCC%" /DAppVersion=%APP_VERSION% installer.iss
if %errorlevel% neq 0 (
    echo.
    echo Compiling the installer failed!
    pause
    exit /b %errorlevel%
)
echo Installer location: installer_output\PokemonDetectorSetup-%APP_VERSION%.exe
echo.
pause
