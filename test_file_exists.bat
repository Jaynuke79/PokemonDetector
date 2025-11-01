@echo off
REM Simple test to verify file existence checking works

echo =========================================
echo Testing File Existence Detection
echo =========================================
echo.

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Test 1: Can we detect detector.py?
if exist "scripts\cli\detector.py" (
    echo   YES - detector.py found
) else (
    echo   NO - detector.py NOT found
)
echo.

echo Test 2: Can we detect class_names.json?
if exist "scripts\cli\class_names.json" (
    echo   YES - class_names.json found
) else (
    echo   NO - class_names.json NOT found
)
echo.

echo Test 3: Can we detect gengar.png?
if exist "scripts\cli\gengar.png" (
    echo   YES - gengar.png found
) else (
    echo   NO - gengar.png NOT found
)
echo.

echo Test 4: Can we detect best_model_fold1.pth?
if exist "scripts\cli\best_model_fold1.pth" (
    echo   YES - best_model_fold1.pth found *** THIS IS THE ONE WE NEED! ***
    echo.
    echo Great! The file exists and batch can detect it.
    echo The build script should work.
) else (
    echo   NO - best_model_fold1.pth NOT found *** PROBLEM! ***
    echo.
    echo The file is not detected by batch script.
    echo.
    echo Possible causes:
    echo 1. File has hidden .txt extension
    echo 2. File has extra spaces in name
    echo 3. File is in wrong location
    echo.
    echo Run these diagnostic scripts:
    echo   - diagnose_model.bat    (detailed file info)
    echo   - fix_model_file.bat    (try automatic fix)
)
echo.

echo =========================================
echo Summary
echo =========================================
echo.
echo All files that SHOULD be detected:
dir /b scripts\cli\
echo.
echo If best_model_fold1.pth appears in the list above
echo but batch says it's NOT found, the filename has
echo hidden characters or extensions.
echo.
pause
