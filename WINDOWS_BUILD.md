# Windows Distribution Guide

This guide explains how to build and distribute the Pokemon Detector as a Windows executable.

## 📋 Prerequisites

### For Building (Developer)
- Windows 10 or later
- Python 3.10 or later
- Git (optional, for cloning)
- At least 2GB of free disk space

### For End Users
- Windows 10 or later
- No Python installation required!
- The executable is self-contained

---

## 🔨 Building the Executable

### Step 1: Download the Model File

Before building, you **must** download the trained model:

1. Download from: [Google Drive Link](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing)
2. Place `best_model_fold1.pth` in the `scripts/cli/` directory

### Step 2: Run the Build Script

Simply double-click `build_windows.bat` or run from command prompt:

```batch
build_windows.bat
```

The script will:
- Create a virtual environment
- Install all dependencies
- Build the executable using PyInstaller
- Place the result in `dist/poke.exe`

**Build time:** Approximately 5-10 minutes (first time)

**Output size:** ~500MB-1GB (includes PyTorch)

---

## 📦 Distribution Package

After building, create a distribution package:

### Option 1: ZIP Archive (Recommended)

Create a folder structure like this:

```
PokemonDetector-Windows/
├── poke.exe              # The main executable
├── README.txt            # User instructions
└── examples/
    └── gengar.png        # Sample image for testing
```

Then compress to `PokemonDetector-Windows.zip`

### Option 2: Installer (Advanced)

For a more professional distribution, consider using:
- **Inno Setup** (free): https://jrsoftware.org/isinfo.php
- **NSIS** (free): https://nsis.sourceforge.io/
- **Advanced Installer** (paid): https://www.advancedinstaller.com/

---

## 🚀 Usage for End Users

### Basic Usage

1. **Extract** the ZIP file to any folder
2. **Open Command Prompt** in that folder (Shift + Right Click → "Open PowerShell window here")
3. **Run** the detector:

```batch
poke.exe path\to\your\image.png
```

### Example

```batch
# Test with included sample
poke.exe examples\gengar.png

# Analyze your own image
poke.exe C:\Users\YourName\Pictures\pokemon.jpg
```

### Command Line Options

```batch
# Show top 5 predictions (default)
poke.exe image.png --topk 5

# Show top 10 predictions
poke.exe image.png --topk 10

# Enable verbose output
poke.exe image.png --verbose True

# Get help
poke.exe --help
```

---

## 📝 Creating a User README

Create a `README.txt` for end users:

```
===========================================
  Pokemon Detector - Windows Edition
===========================================

QUICK START:

1. Open Command Prompt in this folder
2. Run: poke.exe your_image.png
3. See the predictions!

EXAMPLE:
  poke.exe examples\gengar.png

OPTIONS:
  --topk 10        Show top 10 predictions
  --verbose True   Show detailed output
  --help          Show all options

SUPPORTED FORMATS:
  PNG, JPG, JPEG, BMP, GIF

GENERATION SUPPORT:
  Currently detects Generation 1 Pokemon only

QUESTIONS?
  GitHub: https://github.com/Jaynuke79/PokemonDetector
===========================================
```

---

## 🎯 Click-to-Run Setup (Drag & Drop)

For the ultimate user experience, create a drag-and-drop interface:

### Create `drop_image_here.bat`:

```batch
@echo off
echo ========================================
echo   Pokemon Detector - Drag & Drop
echo ========================================
echo.

if "%~1"=="" (
    echo Please drag and drop an image file onto this script!
    echo.
    pause
    exit /b
)

echo Analyzing: %~1
echo.
poke.exe "%~1" --topk 5
echo.
echo ========================================
pause
```

**Usage:** Users can drag any image file onto `drop_image_here.bat` to analyze it!

---

## 🔧 Troubleshooting

### Build Issues

**Problem:** "Model file not found"
- **Solution:** Download and place `best_model_fold1.pth` in `scripts/cli/`

**Problem:** "PyInstaller not found"
- **Solution:** Run `pip install pyinstaller` manually

**Problem:** "Out of memory during build"
- **Solution:** Close other applications and try again

### Runtime Issues

**Problem:** "Missing DLL" errors
- **Solution:** Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

**Problem:** Slow first run
- **Solution:** Normal! PyTorch initialization takes a few seconds

**Problem:** "CUDA not found" (if user has GPU)
- **Solution:** This build uses CPU version of PyTorch (compatible with all systems)

---

## 📊 Build Configuration

### File Sizes
- Source code: ~50MB
- Built executable: ~500MB-1GB (includes PyTorch CPU)
- Full distribution ZIP: ~550MB-1.1GB

### Included Dependencies
- PyTorch (CPU version)
- torchvision
- timm (PyTorch Image Models)
- Click (CLI framework)
- NumPy
- Pillow (PIL)

### Excluded Dependencies
- CUDA (GPU support) - reduces size significantly
- Development tools (Jupyter, notebooks)
- Matplotlib, Pandas (not needed for inference)

---

## 🌟 Advanced Options

### GPU Support

To build with GPU support (larger file size):

1. Edit `build_windows.bat`
2. Change the torch installation line to:
   ```batch
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```
3. Rebuild

**Note:** GPU version will be ~2-3GB larger but much faster on compatible systems.

### Custom Icon

1. Create or download a `.ico` file (e.g., `pokemon.ico`)
2. Edit `poke.spec`
3. Change `icon=None` to `icon='pokemon.ico'`
4. Rebuild

### Code Signing (Optional)

For professional distribution:
1. Obtain a code signing certificate
2. Use `signtool.exe` (Windows SDK) to sign the executable
3. This removes "Unknown Publisher" warnings

---

## 📋 Distribution Checklist

Before distributing to users:

- [ ] Model file is included in build
- [ ] Tested executable on clean Windows machine
- [ ] Created user-friendly README.txt
- [ ] Included example images
- [ ] Tested all command-line options
- [ ] Scanned for viruses (some antiviruses flag PyInstaller executables)
- [ ] Created ZIP with clear folder structure
- [ ] Verified file size is reasonable
- [ ] Tested drag-and-drop batch file (if included)

---

## 🔗 Additional Resources

- **PyInstaller Documentation:** https://pyinstaller.org/
- **PyTorch Documentation:** https://pytorch.org/docs/
- **Click Documentation:** https://click.palletsprojects.com/

---

## 📝 License & Attribution

Make sure your distribution includes:
- License file (if applicable)
- Attribution for PyTorch, timm, and other libraries
- Link to source repository

---

**Built with ❤️ using PyInstaller and PyTorch**
