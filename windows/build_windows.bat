@echo off
setlocal
REM Builds the Windows executables and, if Inno Setup is installed, the installer.
REM Run on Windows with Python 3.11 or newer. GitHub Actions builds with this script too.
REM Parentheses in echoed text or expanded paths would end an if block early, so errors go to labels.

cd /d "%~dp0"
echo ===================================
echo Pokemon Detector Windows Build
echo ===================================
echo Current directory: %CD%
echo.

if not exist "..\cli\main.py" goto :missing_project
if not exist "..\models\class_names.json" goto :missing_project
if not exist "..\models\best_model_fold1.pth" goto :missing_model
echo [OK] Model file found: best_model_fold1.pth
echo.

REM .venv can belong to Linux when the repo is shared with WSL, so Windows keeps its own.
REM This path is relative and has no spaces, which the for /f below relies on.
set "VENV_PYTHON=..\.venv-win\Scripts\python.exe"
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if not errorlevel 1 goto :venv_ready
if exist "..\.venv-win" rmdir /s /q "..\.venv-win"
echo Creating virtual environment...
python -m venv "..\.venv-win"
if errorlevel 1 goto :venv_failed
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 goto :venv_failed
:venv_ready

echo Installing dependencies...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :install_failed
"%VENV_PYTHON%" -m pip install --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.7.1+cpu torchvision==0.22.1+cpu
if errorlevel 1 goto :install_failed
"%VENV_PYTHON%" -m pip install -r ..\requirements.txt pyinstaller==6.22.3 pyinstaller-hooks-contrib==2026.9
if errorlevel 1 goto :install_failed
"%VENV_PYTHON%" -m pip check
if errorlevel 1 goto :install_failed

echo.
echo Building executables...
"%VENV_PYTHON%" -m PyInstaller --noconfirm --clean poke.spec
if errorlevel 1 goto :build_failed
"%VENV_PYTHON%" check_bundled_runtime.py dist\PokemonDetector
if errorlevel 1 goto :runtime_check_failed

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
if exist "%ISCC%" goto :compile_installer
set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" goto :compile_installer
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" goto :compile_installer
echo To build the installer, install Inno Setup 6 from https://jrsoftware.org/isinfo.php
echo and run this script again.
echo.
pause
exit /b 0

:compile_installer
echo Compiling the installer with %ISCC%
set "APP_VERSION="
for /f "usebackq delims=" %%V in (`%VENV_PYTHON% -c "import tomllib; print(tomllib.load(open('../pyproject.toml', 'rb'))['project']['version'])"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION goto :version_failed
"%ISCC%" /Qp /DAppVersion=%APP_VERSION% installer.iss
if errorlevel 1 goto :compile_failed
echo Installer location: installer_output\PokemonDetectorSetup-%APP_VERSION%.exe
echo.
pause
exit /b 0

:missing_project
echo ================================================================
echo ERROR: Project files not found. Expected, next to this windows\ folder:
echo   cli\main.py
echo   lib\detector_core.py
echo   models\class_names.json
echo ================================================================
goto :fail

:missing_model
echo ================================================================
echo ERROR: Model file not found!
echo.
echo Expected location: %CD%\..\models\best_model_fold1.pth
echo.
echo Please download the model from:
echo https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
echo.
echo The filename must be exactly best_model_fold1.pth. Browsers can add a
echo number or a hidden .txt extension; fix_model_file.bat renames those.
echo ================================================================
goto :fail

:venv_failed
echo ERROR: Could not create the virtual environment in .venv-win. Is Python on PATH?
goto :fail

:install_failed
echo ERROR: Installing dependencies failed!
goto :fail

:build_failed
echo ERROR: PyInstaller failed!
goto :fail

:runtime_check_failed
echo ERROR: The bundle is missing a Visual C++ runtime DLL it needs.
goto :fail

:version_failed
echo ERROR: Could not read the version from pyproject.toml.
goto :fail

:compile_failed
echo ERROR: Compiling the installer failed!
goto :fail

:fail
echo.
pause
exit /b 1
