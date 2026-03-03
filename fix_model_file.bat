@echo off
REM Quick fix script for common model file issues

echo =========================================
echo Model File Quick Fix
echo =========================================
echo.

cd /d "%~dp0"

echo Checking for common issues...
echo.

REM Check for .txt extension
if exist "scripts\cli\best_model_fold1.pth.txt" (
    echo FOUND PROBLEM: File has hidden .txt extension
    echo Fixing: Renaming best_model_fold1.pth.txt to best_model_fold1.pth
    ren "scripts\cli\best_model_fold1.pth.txt" "best_model_fold1.pth"
    if %errorlevel% equ 0 (
        echo SUCCESS: File renamed!
        echo You can now run build_windows.bat
    ) else (
        echo ERROR: Could not rename file. You may need to do it manually.
    )
    echo.
    pause
    exit /b 0
)

REM Check for numbered files (browser downloads)
if exist "scripts\cli\best_model_fold1 (1).pth" (
    echo FOUND PROBLEM: File has (1) in the name
    echo Fixing: Renaming to correct name
    ren "scripts\cli\best_model_fold1 (1).pth" "best_model_fold1.pth"
    if %errorlevel% equ 0 (
        echo SUCCESS: File renamed!
        echo You can now run build_windows.bat
    ) else (
        echo ERROR: Could not rename file. You may need to do it manually.
    )
    echo.
    pause
    exit /b 0
)

REM Check if file exists with correct name
if exist "scripts\cli\best_model_fold1.pth" (
    echo GOOD NEWS: File exists with correct name!
    echo.
    for %%F in ("scripts\cli\best_model_fold1.pth") do (
        echo Full path: %%~fF
        echo File size: %%~zF bytes
        echo Expected: ~300-500 MB (300000000-500000000 bytes)
        echo.
        if %%~zF LSS 100000000 (
            echo WARNING: File seems too small! It may be corrupted.
            echo Please re-download from Google Drive.
        ) else (
            echo File size looks good!
            echo.
            echo The file is in the correct location with the correct name.
            echo If build_windows.bat still can't find it, this might be
            echo a batch file issue. Try running:
            echo   build_windows.bat
            echo.
            echo from this exact directory: %CD%
        )
    )
    echo.
    pause
    exit /b 0
)

REM If we get here, file not found at all
echo NO MODEL FILE FOUND in scripts\cli\
echo.
echo Please check:
echo 1. Did you download the file from Google Drive?
echo 2. Did you save it in the scripts\cli\ folder?
echo.
echo Download link:
echo https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
echo.
echo Save location: %CD%\scripts\cli\best_model_fold1.pth
echo.
echo Current files in scripts\cli\:
dir /b scripts\cli\
echo.
pause
