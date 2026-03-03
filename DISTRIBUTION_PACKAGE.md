# Distribution Package Structure

This document describes how to package the built executable for end-user distribution.

## 📦 Recommended Package Structure

After building with `build_windows.bat`, create this folder structure:

```
PokemonDetector-Windows-v1.0/
│
├── poke.exe                    # Main executable (built by PyInstaller)
├── drop_image_here.bat         # Drag-and-drop interface
├── USER_README.txt             # User instructions
│
├── examples/                   # Sample images for testing
│   ├── gengar.png
│   └── (add more sample images)
│
└── requirements_install/       # Optional: installers for dependencies
    └── vc_redist.x64.exe      # Visual C++ Redistributable (optional)
```

## 🔨 Creating the Distribution Package

### Step 1: Build the Executable

```batch
# On a Windows machine
build_windows.bat
```

This creates `dist/poke.exe`

### Step 2: Create Distribution Folder

```batch
mkdir PokemonDetector-Windows-v1.0
cd PokemonDetector-Windows-v1.0
```

### Step 3: Copy Files

```batch
# Copy the executable
copy ..\dist\poke.exe .

# Copy batch files
copy ..\drop_image_here.bat .

# Copy user documentation
copy ..\USER_README.txt .

# Create and populate examples folder
mkdir examples
copy ..\scripts\cli\gengar.png examples\
```

### Step 4: Create ZIP Archive

Use Windows built-in compression or 7-Zip:

```batch
# Right-click folder -> Send to -> Compressed (zipped) folder
# Or use 7-Zip for better compression
7z a -tzip PokemonDetector-Windows-v1.0.zip PokemonDetector-Windows-v1.0\
```

## 📊 Expected File Sizes

| Component | Size (Approx) |
|-----------|--------------|
| poke.exe | 500MB - 1GB |
| drop_image_here.bat | 1 KB |
| USER_README.txt | 3 KB |
| examples/*.png | 100-500 KB each |
| **Total ZIP** | **~500MB - 1GB** |

## 🎯 Distribution Methods

### Method 1: Direct Download (GitHub Releases)

1. Go to GitHub repository
2. Create a new Release
3. Upload the ZIP file
4. Add release notes

**Pros:** Free, version controlled, trackable downloads
**Cons:** GitHub has file size limits (2GB max, but works for this)

### Method 2: Cloud Storage

Upload to:
- Google Drive
- Dropbox
- OneDrive
- Mega.nz (for larger files)

**Pros:** Easy sharing, no size limits
**Cons:** Requires cloud storage account

### Method 3: Self-Hosted

Host on your own server/website

**Pros:** Full control
**Cons:** Requires server and bandwidth

## 📝 Release Checklist

Before distributing:

- [ ] Built on Windows 10/11
- [ ] Tested on clean Windows machine (no Python installed)
- [ ] All sample images work
- [ ] Drag-and-drop batch file works
- [ ] USER_README.txt is clear and accurate
- [ ] Version number is correct
- [ ] File size is documented
- [ ] Virus scanned (VirusTotal.com)
- [ ] Release notes written
- [ ] License file included (if applicable)

## 🔒 Security Notes

### Antivirus False Positives

PyInstaller executables often trigger false positives. To minimize this:

1. **Scan with VirusTotal** before distribution
2. **Code sign** the executable (requires certificate)
3. **Provide hash** (SHA256) for verification
4. **Document** known false positives in README

### Generate SHA256 Hash

On Windows:

```batch
certutil -hashfile poke.exe SHA256
```

Include this hash in your release notes so users can verify authenticity.

## 📋 Sample Release Notes

```markdown
# Pokemon Detector v1.0 - Windows Release

## What's New
- Initial Windows executable release
- Drag-and-drop interface for easy use
- CPU-based inference (works on any PC)
- Generation 1 Pokemon detection (151 species)

## Download
- **File:** PokemonDetector-Windows-v1.0.zip
- **Size:** 550 MB
- **SHA256:** [insert hash here]

## System Requirements
- Windows 10 or later (64-bit)
- 2 GB RAM minimum
- 1.5 GB free disk space

## Installation
1. Extract ZIP file
2. Read USER_README.txt
3. Run poke.exe or drag images onto drop_image_here.bat

## Known Issues
- First run may be slow (10-30 seconds) - this is normal
- Some antivirus software may flag the executable (false positive)
- Requires Visual C++ Redistributable (included in Windows 10+)

## Support
Report issues: [GitHub Issues URL]

## Credits
Built with PyTorch, timm, and PyInstaller
```

## 🚀 Advanced Distribution: Installer

For a professional installer experience, consider using **Inno Setup** (free):

### Inno Setup Script Example

Create `installer.iss`:

```pascal
[Setup]
AppName=Pokemon Detector
AppVersion=1.0
DefaultDirName={pf}\PokemonDetector
DefaultGroupName=Pokemon Detector
OutputDir=installer_output
OutputBaseFilename=PokemonDetectorSetup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\poke.exe"; DestDir: "{app}"
Source: "drop_image_here.bat"; DestDir: "{app}"
Source: "USER_README.txt"; DestDir: "{app}"
Source: "examples\*"; DestDir: "{app}\examples"

[Icons]
Name: "{group}\Pokemon Detector"; Filename: "{app}\poke.exe"
Name: "{group}\User Manual"; Filename: "{app}\USER_README.txt"
Name: "{group}\Drag and Drop"; Filename: "{app}\drop_image_here.bat"

[Run]
Filename: "{app}\USER_README.txt"; Description: "View User Manual"; Flags: postinstall shellexec skipifsilent
```

Compile with Inno Setup to create `PokemonDetectorSetup.exe` (~500MB)

## 📱 Alternative: Portable Version

For users who prefer portable software:

1. Package everything in a single folder
2. Add "PORTABLE" to the folder name
3. Include note that no installation is required
4. Everything runs from the folder

## 🌐 Distribution Platforms

Consider publishing on:

### Free Platforms
- **GitHub Releases** - Best for developers
- **SourceForge** - Traditional software distribution
- **itch.io** - Great for game-related tools
- **Archive.org** - Permanent archival

### Paid/Commercial Platforms
- **Steam** (if applicable)
- **Microsoft Store** (requires certification)
- **Gumroad** (for paid distribution)

## 📊 Download Tracking

To track downloads:

- GitHub Releases: Built-in download counter
- Google Drive: View count in sharing settings
- Custom domain: Use Google Analytics
- Bitly: Create short link with analytics

## 🔄 Update Strategy

For future versions:

1. **Semantic Versioning:** v1.0.0, v1.1.0, v2.0.0
2. **Changelog:** Document all changes
3. **Backward Compatibility:** Note breaking changes
4. **Migration Guide:** Help users upgrade

Example folder structure for updates:

```
Releases/
├── v1.0/
│   └── PokemonDetector-Windows-v1.0.zip
├── v1.1/
│   └── PokemonDetector-Windows-v1.1.zip
└── latest/
    └── PokemonDetector-Windows-latest.zip (symlink)
```

---

## 📞 Support Documentation

Create a support page with:

- **FAQ** - Common questions
- **Troubleshooting** - Known issues
- **Video Tutorial** - YouTube walkthrough
- **Contact** - Email or Discord for help

---

**Happy Distributing! 🎉**
