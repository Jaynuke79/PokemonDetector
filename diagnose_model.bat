@echo off
REM Detailed diagnostic for the model file specifically
REM This will help identify hidden extensions, extra spaces, etc.

echo =========================================
echo Model File Detection Diagnostic
echo =========================================
echo.

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Looking for: best_model_fold1.pth
echo In directory: scripts\cli\
echo.

echo =========================================
echo Method 1: Basic dir command
echo =========================================
dir scripts\cli\best_model_fold1.pth
echo.

echo =========================================
echo Method 2: All files in scripts\cli
echo =========================================
dir scripts\cli\
echo.

echo =========================================
echo Method 3: All .pth files
echo =========================================
dir scripts\cli\*.pth
echo.

echo =========================================
echo Method 4: Files with 'best_model' in name
echo =========================================
dir scripts\cli\best_model*
echo.

echo =========================================
echo Method 5: All files (including hidden)
echo =========================================
dir /a scripts\cli\
echo.

echo =========================================
echo Method 6: Check for .txt extension hidden
echo =========================================
if exist "scripts\cli\best_model_fold1.pth.txt" (
    echo FOUND: best_model_fold1.pth.txt ^(hidden extension!^)
    echo.
    echo The file has a hidden .txt extension!
    echo To fix: Rename the file to remove .txt
    echo.
    echo Commands to fix:
    echo   ren "scripts\cli\best_model_fold1.pth.txt" "best_model_fold1.pth"
) else (
    echo Not found: best_model_fold1.pth.txt
)
echo.

echo =========================================
echo Method 7: Check exact filename with quotes
echo =========================================
if exist "scripts\cli\best_model_fold1.pth" (
    echo SUCCESS: File exists with exact name!
    echo.
    for %%F in ("scripts\cli\best_model_fold1.pth") do (
        echo Full path: %%~fF
        echo File size: %%~zF bytes
        echo Date/Time: %%~tF
    )
) else (
    echo FAILED: File not found with exact name
)
echo.

echo =========================================
echo Method 8: List all files with full details
echo =========================================
echo Full listing of scripts\cli\:
for %%F in ("scripts\cli\*") do (
    echo   - %%~nxF ^(%%~zF bytes^)
)
echo.

echo =========================================
echo Method 9: Check file attributes
echo =========================================
if exist "scripts\cli\best_model_fold1.pth" (
    attrib "scripts\cli\best_model_fold1.pth"
) else (
    echo Cannot check attributes - file not found
)
echo.

echo =========================================
echo DIAGNOSIS COMPLETE
echo =========================================
echo.
echo What to look for:
echo 1. If you see the file but with .txt extension, rename it
echo 2. If file size is very small ^(^<1MB^), it might be corrupted
echo 3. Expected file size: ~300-500 MB
echo 4. Check for extra spaces or characters in the filename
echo.
echo If the file exists but still not detected:
echo Try manually checking the exact filename in File Explorer
echo with "File name extensions" enabled in View menu.
echo.
pause
