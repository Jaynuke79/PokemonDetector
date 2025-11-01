@echo off
REM Diagnostic script to help debug path issues
REM Run this to see what the build script sees

echo =========================================
echo Pokemon Detector - Diagnostic Script
echo =========================================
echo.

echo 1. Where am I running from?
echo    %~dp0
echo.

echo 2. Current working directory BEFORE cd:
echo    %CD%
echo.

cd /d "%~dp0"

echo 3. Current working directory AFTER cd:
echo    %CD%
echo.

echo 4. Contents of current directory:
dir /b
echo.

echo 5. Does 'scripts' folder exist?
if exist "scripts" (
    echo    YES - scripts folder exists
) else (
    echo    NO - scripts folder NOT found
)
echo.

echo 6. Does 'scripts\cli' folder exist?
if exist "scripts\cli" (
    echo    YES - scripts\cli folder exists
) else (
    echo    NO - scripts\cli folder NOT found
)
echo.

echo 7. Trying different path variations:
if exist "scripts\cli\" (
    echo    - scripts\cli\ (with trailing slash) = EXISTS
) else (
    echo    - scripts\cli\ (with trailing slash) = NOT FOUND
)

if exist "scripts\cli" (
    echo    - scripts\cli (no trailing slash) = EXISTS
) else (
    echo    - scripts\cli (no trailing slash) = NOT FOUND
)

if exist ".\scripts\cli" (
    echo    - .\scripts\cli (with dot) = EXISTS
) else (
    echo    - .\scripts\cli (with dot) = NOT FOUND
)
echo.

echo 8. If scripts\cli exists, what's inside?
if exist "scripts\cli" (
    echo    Contents of scripts\cli:
    dir /b scripts\cli
) else (
    echo    Cannot list - directory not found
)
echo.

echo 9. Looking for the model file specifically:
if exist "scripts\cli\best_model_fold1.pth" (
    echo    FOUND: scripts\cli\best_model_fold1.pth
    dir scripts\cli\best_model_fold1.pth
) else (
    echo    NOT FOUND: scripts\cli\best_model_fold1.pth
)
echo.

echo 10. Full directory tree:
tree /F /A
echo.

echo =========================================
echo Diagnostic complete!
echo.
echo Please share this output to help debug the issue.
echo =========================================
pause
