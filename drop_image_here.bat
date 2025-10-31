@echo off
REM Drag-and-drop interface for Pokemon Detector
REM Users can drag image files onto this script for instant detection

echo ========================================
echo   Pokemon Detector - Drag ^& Drop
echo ========================================
echo.

if "%~1"=="" (
    echo Please drag and drop an image file onto this script!
    echo.
    echo Supported formats: PNG, JPG, JPEG, BMP, GIF
    echo.
    pause
    exit /b
)

echo Analyzing: %~nx1
echo Full path: %~1
echo.
echo Detecting Pokemon...
echo ----------------------------------------
echo.

REM Call poke.exe with the dropped file
"%~dp0poke.exe" "%~1" --topk 5

echo.
echo ========================================
echo Analysis complete!
echo ========================================
pause
