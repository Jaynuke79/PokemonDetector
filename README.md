# PokemonDetector

A Pokemon detection system using a PyTorch-based ConvNeXt model to identify Pokemon from images.

Originally built as a class project, this repository demonstrates modern project development and management practices with clearly separated outputs.

---

## 📦 Project Outputs

This project provides **2 functional outputs** and **1 deployment method**:

### Functional Outputs

1. **CLI Tool** (`poke` command) - Command-line interface for quick predictions
2. **Web Application** - Flask-based web interface with image upload

### Deployment Method

3. **Docker Container** - Containerized deployment of the web application

---

## 🗂️ Directory Structure

```
pokemonDetector/
├── cli/                    # CLI Tool Output
│   ├── __init__.py
│   └── main.py            # CLI interface
│
├── webapp/                # Web Application Output
│   ├── app.py             # Flask application
│   ├── templates/         # HTML templates
│   └── static/            # Static assets
│
├── lib/                   # Shared Core Library
│   ├── __init__.py
│   └── detector_core.py   # Model loading & prediction logic
│
├── deployment/            # Docker Deployment Method
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.config
│
├── models/                # Model Files (see models/README.md)
│   ├── best_model_fold1.pth      # Download required
│   └── class_names.json          # Download required
│
└── pyproject.toml         # Project configuration
```

---

## 🚀 Quick Start

### Prerequisites

1. **Install UV** (Python package manager)
2. **Download Model Files** - See [models/README.md](models/README.md) for instructions

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd pokemonDetector

# Activate UV environment
source .venv/bin/activate

# Install dependencies
uv sync
```

---

## 🎯 Using the Outputs

### 1. CLI Tool

```bash
# Basic prediction
uv run poke path/to/image.jpg

# Top 3 predictions with verbose output
uv run poke path/to/image.jpg --topk 3 --verbose true

# Custom model weights
uv run poke path/to/image.jpg --weights models/best_model_fold1.pth --class-names-path models/class_names.json
```

### 2. Web Application (Local)

```bash
# Run Flask app
python webapp/app.py

# Access at http://localhost:5000
```

Upload an image through the web interface to get top 5 predictions.

### 3. Docker Deployment

```bash
# Navigate to deployment directory
cd deployment

# Build and run with docker compose
docker compose up --build

# Access at http://localhost:5000
# Optional nginx reverse proxy at http://localhost:80

# Stop services
docker compose down
```

---

## 🏗️ Architecture

All outputs share the same core detection logic from `lib/detector_core.py`:

- **Model**: ConvNeXt base architecture (via `timm` library)
- **Input**: Images resized to 224x224, normalized with ImageNet stats
- **Output**: Top-k predictions with confidence scores
- **Classes**: 151 Pokemon (Generation 1)

**Shared Library (`lib/detector_core.py`):**
- `load_class_names()` - Load Pokemon class labels
- `load_model()` - Initialize ConvNeXt model with weights
- `get_device()` - Detect CUDA/CPU
- `get_transform()` - Image preprocessing pipeline
- `predict_image()` - Run inference and return top-k results

**CLI Tool** imports the library and provides a Click-based command interface.

**Web Application** imports the library and wraps it in Flask routes with HTML upload form.

**Docker Deployment** containerizes the web application with volume mounts for model files.

---

## 📝 Technologies

- **UV** - Python package management
- **PyTorch** - Deep learning framework
- **TIMM** - Pre-trained model library
- **Click** - CLI framework
- **Flask** - Web framework
- **Docker** - Containerization

---

## ⚠️ Important Notes

- Model files (`best_model_fold1.pth`, `class_names.json`) are **not** in version control
- Download them from [Google Drive](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing)
- Place them in the `models/` directory
- The model is trained on Generation 1 Pokemon only (151 classes)

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
