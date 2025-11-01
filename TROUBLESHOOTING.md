# Build Troubleshooting Guide

Having issues building the Windows executable? This guide will help you diagnose and fix common problems.

## 🔬 First Step: Run the Diagnostic Script

**Before anything else, run this:**

```batch
diagnose.bat
```

This will show you:
- Where the script thinks it is
- What directories exist
- What files are in scripts/cli
- Whether the model file is found

Copy the output and use it to help debug the issue. It will save you a lot of time!

---

## 🔍 Model File Not Found

### Symptom
Build script stops with:
```
WARNING: Model file not found at scripts\cli\best_model_fold1.pth
```

### Diagnosis Steps

**0. Run the diagnostic script first:**
```batch
diagnose.bat
```

**1. Check if you downloaded the model:**
```batch
dir scripts\cli\best_model_fold1.pth
```

If you see "File Not Found", you need to download it.

**1b. Check if the scripts directory exists:**
```batch
dir scripts\cli
```

If you get "The system cannot find the path specified", the directory structure is missing.

**2. Check the file name exactly:**
The file must be named **exactly**: `best_model_fold1.pth`

Common mistakes:
- ❌ `best_model_fold1.pth.txt` (Windows hid the .txt extension)
- ❌ `best_model_fold1 (1).pth` (browser added number)
- ❌ `best_model_fold1.PTH` (wrong case, though usually OK on Windows)

**3. Check the file location:**
```
PokemonDetector/          ← Your project root
├── build_windows.bat     ← Build script here
├── scripts/
│   └── cli/
│       ├── best_model_fold1.pth  ← Model MUST be here
│       ├── class_names.json
│       ├── detector.py
│       └── gengar.png
```

**4. Run the build script from the correct location:**
You MUST run `build_windows.bat` from the project root directory.

❌ Wrong:
```
C:\Users\You\Downloads> build_windows.bat
```

✅ Correct:
```
C:\Users\You\PokemonDetector> build_windows.bat
```

### Solutions

**Solution 1: Download the Model**
1. Go to: https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
2. Click "Download"
3. Save to `scripts\cli\best_model_fold1.pth`

**Solution 2: Check File Extension**
Windows hides file extensions by default. To show them:
1. Open File Explorer
2. Click "View" tab
3. Check "File name extensions"
4. Check if the file is actually `best_model_fold1.pth.txt`
5. If so, rename to remove `.txt`

**Solution 3: Use Full Path**
If the relative path doesn't work, try copying the file using full path:
```batch
copy C:\Users\YourName\Downloads\best_model_fold1.pth C:\Users\YourName\PokemonDetector\scripts\cli\
```

**Solution 4: Check Directory Structure**
Make sure you have the complete directory structure. Run:
```batch
tree /F scripts
```

You should see:
```
scripts
└───cli
    ├── best_model_fold1.pth
    ├── class_names.json
    ├── detector.py
    └── gengar.png
```

---

## 🐍 Python Not Found

### Symptom
```
'python' is not recognized as an internal or external command
```

### Solution
Install Python 3.10 or later:
1. Download from: https://www.python.org/downloads/
2. **Important:** Check "Add Python to PATH" during installation
3. Restart your command prompt
4. Verify: `python --version`

---

## 📦 PyInstaller Build Fails

### Symptom
```
Error loading Python DLL
ModuleNotFoundError: No module named 'torch'
```

### Solutions

**Solution 1: Clean Rebuild**
```batch
REM Delete virtual environment
rmdir /s /q .venv

REM Delete build artifacts
rmdir /s /q build
rmdir /s /q dist

REM Run build again
build_windows.bat
```

**Solution 2: Manual Dependency Installation**
```batch
.venv\Scripts\activate.bat
pip install --upgrade pip
pip install pyinstaller
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install timm click numpy pillow
pyinstaller --clean poke.spec
```

**Solution 3: Check Python Version**
```batch
python --version
```
Must be Python 3.10 or newer. If not, update Python.

---

## 💾 Out of Disk Space

### Symptom
```
Error: No space left on device
```

### Solution
You need at least **2GB free space**:
- Virtual environment: ~500MB
- PyTorch CPU: ~500MB
- Build artifacts: ~1GB

Free up space and try again.

---

## 🐌 Build is Very Slow

### Symptom
Build takes more than 15 minutes

### This is Normal If:
- ✅ First time building (10-15 minutes)
- ✅ Downloading PyTorch (~500MB)
- ✅ Slow internet connection

### This is NOT Normal If:
- ❌ Build takes more than 30 minutes
- ❌ CPU usage is at 100% for extended period
- ❌ Subsequent builds also take 15+ minutes

### Solution
1. Close other applications
2. Ensure antivirus isn't scanning every file (add exclusion)
3. Try on a faster machine or use `--noconfirm` flags

---

## 🔒 Antivirus Blocking Build

### Symptom
- PyInstaller fails with permission errors
- `.exe` file disappears after build
- "Access denied" errors

### Solution
Temporarily disable antivirus or add exclusions for:
- Project directory
- `.venv` directory
- `dist` directory
- `pyinstaller.exe`

---

## 📋 Build Succeeds but EXE Won't Run

### Symptom
Double-clicking `poke.exe` shows error or nothing happens

### Diagnosis
Run from command prompt to see error:
```batch
dist\poke.exe
```

### Common Errors & Solutions

**"Missing DLL"**
→ Install Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

**"Model file not found"**
→ The model was not included in the build. Rebuild after placing model file correctly.

**"CUDA not available"**
→ This is OK! The CPU version is being used. Ignore this message.

---

## 🔧 Advanced Diagnostics

### Check Build Output
Look at the PyInstaller output carefully:
```
WARNING: Hidden import not found: some_module
```
These might need to be added to `poke.spec` under `hiddenimports`.

### Test in Clean Environment
1. Copy `dist\poke.exe` to another computer without Python
2. Try running it there
3. This tests if it's truly standalone

### Check File Size
The executable should be **500MB - 1GB**.

If it's much smaller (<100MB), something went wrong.

---

## 🆘 Still Having Issues?

### Get Help
1. **Check the output:** The script now shows what directory it's checking
2. **List files:** Run `dir scripts\cli\` to see what's actually there
3. **Take screenshots:** Capture the error messages
4. **Report issue:** https://github.com/Jaynuke79/PokemonDetector/issues

### Include in Bug Report
- [ ] Operating System (Windows 10/11, version)
- [ ] Python version (`python --version`)
- [ ] Full error message
- [ ] Contents of `scripts\cli\` directory
- [ ] Screenshot of the error
- [ ] Steps you've already tried

---

## 🔍 Directory Not Found Error

### Symptom
```
ERROR: 'scripts' directory not found!
```
or
```
ERROR: 'scripts\cli' directory not found!
```

### Cause
The project structure is incomplete or you're in the wrong directory.

### Solutions

**Solution 1: Verify Project Structure**

Run these commands to check:
```batch
dir
dir scripts
dir scripts\cli
```

You should see:
- `build_windows.bat` in the root
- `scripts` folder in the root
- `cli` folder inside scripts
- Files inside `scripts\cli`: detector.py, class_names.json, gengar.png

**Solution 2: Re-clone/Re-download the Project**

If directories are missing:
```batch
git clone https://github.com/Jaynuke79/PokemonDetector.git
cd PokemonDetector
```

**Solution 3: Check if You Extracted ZIP Correctly**

If you downloaded a ZIP file, make sure you:
1. Extracted ALL folders (not just files)
2. Didn't extract into a nested folder
3. Have the complete directory structure

**Solution 4: Create Missing Directories**

If only the directories are missing (files exist elsewhere):
```batch
mkdir scripts
mkdir scripts\cli
REM Then move the Python files into scripts\cli\
```

---

## 📝 Quick Checklist

Before building, verify:

- [ ] Downloaded model file from Google Drive
- [ ] Saved as `scripts/cli/best_model_fold1.pth` (exact name!)
- [ ] Python 3.10+ installed
- [ ] Running from project root directory
- [ ] Have 2GB+ free disk space
- [ ] Not running from OneDrive/Dropbox (use local folder)

If all checked, run `build_windows.bat` and it should work!

---

**Good luck! 🍀**
