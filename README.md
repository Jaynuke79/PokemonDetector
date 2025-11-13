# PokemonDetector

A web application that detects Pokémon from images.  
Originally built as a class project, this repository demonstrates modern project development and management practices.

---

## 🚀 Project Goals

- **Familiarize with project management tools**
- **Containerize with Docker**
- **Develop frontend with Replit**
- **Implement ML with PyTorch**

---

## 🗂️ Directory Structure

| Directory      | Purpose                        |
| -------------- | ----------------------------- |
| **app/**       | Web server & API code          |
| **data/**      | Datasets and related files     |
| **frontend/**  | Frontend (UI) source code      |
| **scripts/**   | Utility and helper scripts     |
| **tests/**     | Automated tests                |

---

## 📦 Deliverable

A web app that hosts a Pokémon detector.

---

## 📝 Project Management

- **UV** for project management
- **Docker** for containerization
- **Replit** for frontend development
- **PyTorch** for machine learning

---

## 🗒️ Walk Throughs

| Topic | Cmds | Note(s) |
|-------|------|---------|
| UV Env Terminal | `source .venv/bin/activate` | Opens Terminal in UV Env as defined in `.venv` <br> _Works as if you put `uv run` in front of all cmds_ |
| CLI Script: `poke` | `uv run poke <img_path>` | Predicts what Pokémon is in the image <br> _Requires downloading of [model](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing) to `scirpts/cli`_ <br> _Default model is trained on Gen1 only_ |

---

## 💻 Windows Executable Distribution

Want to share this with non-technical users on Windows? Build a click-to-run executable!

### For End Users (No Python Required!)

Download the pre-built Windows executable and simply:
1. **Drag and drop** an image onto `drop_image_here.bat`
2. **Or run** from command line: `poke.exe your_image.png`

See [USER_README.txt](USER_README.txt) for complete user instructions.

### For Developers (Building the Executable)

Build a standalone Windows executable that includes all dependencies:

```batch
# On Windows, run:
build_windows.bat
```

This creates `dist/poke.exe` (~500MB-1GB, includes PyTorch).

**Documentation:**
- **[WINDOWS_BUILD.md](WINDOWS_BUILD.md)** - Complete build instructions and troubleshooting
- **[DISTRIBUTION_PACKAGE.md](DISTRIBUTION_PACKAGE.md)** - How to package and distribute

**Features:**
- ✅ Single executable file
- ✅ No Python installation required
- ✅ Includes all dependencies (PyTorch, timm, etc.)
- ✅ Drag-and-drop interface
- ✅ Works on any Windows 10+ machine

---

Feel free to explore the directories and contribute!