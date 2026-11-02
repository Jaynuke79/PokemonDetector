@echo off
setlocal
REM Quick fix script for common model file issues
REM Parentheses in echoed text or expanded paths would end an if block early, so branches go to labels.

echo =========================================
echo Model File Quick Fix
echo =========================================
echo.

cd /d "%~dp0"

echo Checking for common issues...
echo.

if exist "..\models\best_model_fold1.pth.txt" goto :hidden_txt_extension
if exist "..\models\best_model_fold1 (1).pth" goto :numbered_download
if exist "..\models\best_model_fold1.pth" goto :model_found

echo NO MODEL FILE FOUND in ..\models\
echo.
echo Please check:
echo 1. Did you download the file from Google Drive?
echo 2. Did you save it in the models\ folder?
echo.
echo Download link:
echo https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
echo.
echo Save location: %CD%\..\models\best_model_fold1.pth
echo.
echo Current files in ..\models\:
dir /b ..\models\
echo.
pause
exit /b 0

:hidden_txt_extension
echo FOUND PROBLEM: File has hidden .txt extension
echo Fixing: Renaming best_model_fold1.pth.txt to best_model_fold1.pth
ren "..\models\best_model_fold1.pth.txt" "best_model_fold1.pth"
goto :after_rename

:numbered_download
echo FOUND PROBLEM: File has a download number in the name
echo Fixing: Renaming to correct name
ren "..\models\best_model_fold1 (1).pth" "best_model_fold1.pth"
goto :after_rename

:after_rename
if errorlevel 1 goto :rename_failed
if not exist "..\models\best_model_fold1.pth" goto :rename_failed
echo SUCCESS: File renamed!
echo You can now run build_windows.bat
echo.
pause
exit /b 0

:rename_failed
echo ERROR: Could not rename file. You may need to do it manually.
echo.
pause
exit /b 1

:model_found
echo GOOD NEWS: File exists with correct name!
echo.
for %%F in ("..\models\best_model_fold1.pth") do set "MODEL_SIZE=%%~zF"
echo Location: %CD%\..\models\best_model_fold1.pth
echo File size: %MODEL_SIZE% bytes
echo Expected: 351007742 bytes
echo.
if %MODEL_SIZE% LSS 100000000 goto :too_small
echo File size looks good!
echo.
echo The file is in the correct location with the correct name.
echo If build_windows.bat still can't find it, run it from this directory:
echo %CD%
echo.
pause
exit /b 0

:too_small
echo WARNING: File seems too small! It may be corrupted.
echo Please re-download from Google Drive.
echo.
pause
exit /b 0
