# Windows Executable - Quick Start Guide

This is a **5-minute guide** to building a Windows executable for Pokemon Detector.

## 🎯 Goal

Create `poke.exe` - a standalone Windows executable that anyone can run without installing Python.

## ⚡ Quick Build (3 Steps)

### 1️⃣ Download the Model

Download the trained model file:
- **Link:** https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
- **Save as:** `scripts/cli/best_model_fold1.pth`

### 2️⃣ Run Build Script

On a Windows machine, double-click:
```
build_windows.bat
```

Or from command prompt:
```batch
build_windows.bat
```

### 3️⃣ Get Your Executable

Find the executable at:
```
dist/poke.exe
```

That's it! 🎉

## 🧪 Test It

```batch
dist\poke.exe scripts\cli\gengar.png
```

Expected output:
```
Class Index: 94, Class Name: Gengar, Confidence: 0.9876
Class Index: 93, Class Name: Haunter, Confidence: 0.0098
...
```

## 📦 Share It

To share with others:

1. Copy `dist/poke.exe` to a new folder
2. Add `drop_image_here.bat` (from project root)
3. Add `USER_README.txt` (from project root)
4. Zip it up and share!

Users just:
- Extract the ZIP
- Drag an image onto `drop_image_here.bat`
- See instant predictions!

## 🚨 Common Issues

**"Model file not found"**
→ Download model file to `scripts/cli/best_model_fold1.pth`

**"PyInstaller not found"**
→ The build script installs it automatically. If it fails, run:
```batch
pip install pyinstaller
```

**Build is slow**
→ Normal! First build takes 5-10 minutes. Be patient.

**Executable is huge (500MB+)**
→ Normal! It includes PyTorch and all dependencies.

**Antivirus flags it**
→ False positive. PyInstaller executables are often flagged. Scan with VirusTotal to confirm.

## 📚 Need More Details?

- **Full build guide:** [WINDOWS_BUILD.md](WINDOWS_BUILD.md)
- **Distribution guide:** [DISTRIBUTION_PACKAGE.md](DISTRIBUTION_PACKAGE.md)
- **User manual:** [USER_README.txt](USER_README.txt)

## 🎓 What's Happening?

The build script:
1. Creates Python virtual environment
2. Installs PyTorch (CPU version) + dependencies
3. Runs PyInstaller with `poke.spec` configuration
4. Bundles everything into single `poke.exe` file

The executable contains:
- Python interpreter
- PyTorch library
- All dependencies (timm, click, numpy, PIL)
- Your model and class names
- Application code

All in one click-to-run file!

## 💡 Pro Tips

**Reduce file size:**
- The CPU version of PyTorch is used (no CUDA = smaller)
- Already excludes dev dependencies (Jupyter, matplotlib, etc.)
- Can't reduce much more without breaking functionality

**Add custom icon:**
1. Get a `.ico` file (e.g., `pokemon.ico`)
2. Edit `poke.spec`
3. Change `icon=None` to `icon='pokemon.ico'`
4. Rebuild

**Speed up builds:**
- PyInstaller caches compiled files
- Subsequent builds are much faster (1-2 minutes)
- Only clean rebuild if having issues

**Cross-compile?**
- ❌ No - Must build on Windows to create Windows .exe
- Use a Windows VM if you're on Mac/Linux
- Or use GitHub Actions (advanced)

---

**Happy building! 🚀**
