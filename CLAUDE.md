# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PokemonDetector is a Pokemon detection system with a PyTorch-based ConvNeXt model to identify Pokemon from images.

**The project has 2 functional outputs and 1 deployment method:**

1. **CLI Tool** (`poke` command) - Command-line interface for quick predictions
2. **Web Application** - Flask-based web interface with image upload
3. **Docker Container** - Containerized deployment method for the web application

All outputs share the same core detection logic from `lib/detector_core.py`.

## Directory Structure

```
pokemonDetector/
├── cli/                    # CLI Tool Output
│   ├── __init__.py
│   └── main.py            # CLI interface using Click
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
├── models/                # Model Files (not in version control)
│   ├── best_model_fold1.pth      # Download required
│   └── class_names.json          # Download required
│
└── pyproject.toml         # Package configuration
```

## Development Commands

### Environment Setup
```bash
# Activate UV virtual environment
source .venv/bin/activate

# Install dependencies
uv sync
```

### Running the Outputs

**1. CLI Tool:**
```bash
# Basic prediction
uv run poke path/to/image.jpg

# With custom options
uv run poke path/to/image.jpg --topk 3 --verbose true

# Custom model weights
uv run poke path/to/image.jpg --weights models/best_model_fold1.pth --class-names-path models/class_names.json
```

**2. Web Application (Local):**
```bash
# Run Flask app
python webapp/app.py

# Access at http://localhost:5000
```

**3. Docker Deployment:**
```bash
# Navigate to deployment directory
cd deployment

# Build and run
docker compose up --build

# Run only app service (without nginx)
docker compose up pokemon-detector

# Stop services
docker compose down

# Access web app: http://localhost:5000
# Access nginx (if enabled): http://localhost:80
```

## Architecture

### Model Requirements

**Required Files** (must be downloaded separately):
- `best_model_fold1.pth` - Pre-trained ConvNeXt model weights
- `class_names.json` - Pokemon class labels (151 classes for Gen1)

**Download:** [Google Drive Link](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing)

**Location:** Place both files in `models/` directory

**Note:** Model files are NOT in version control. Applications will start without them but predictions will fail with informative errors.

### Core Components

**Shared Library (`lib/detector_core.py`):**
- `load_class_names()` - Load Pokemon class names from JSON
- `load_model()` - Initialize ConvNeXt model with pre-trained weights
- `get_device()` - Detect CUDA GPU or fallback to CPU
- `get_transform()` - Image preprocessing pipeline (resize 224x224, normalize)
- `predict_image()` - Run inference and return top-k predictions

**CLI Tool (`cli/main.py`):**
- Imports functions from `lib.detector_core`
- Click-based command-line interface
- Accepts image path and options (topk, verbose, custom weights)
- Outputs predictions to stdout
- Entry point: `poke` command defined in `pyproject.toml`

**Web Application (`webapp/app.py`):**
- Imports functions from `lib.detector_core`
- Flask server with routes: `/` (upload form), `/predict` (API), `/health` (status)
- Loads model globally on startup
- Accepts image uploads (max 16MB, formats: png/jpg/jpeg/gif/bmp)
- Returns JSON with top 5 predictions and confidence scores
- Templates in `webapp/templates/`, static assets in `webapp/static/`

**Docker Deployment (`deployment/`):**
- Dockerfile: Python 3.10-slim, installs from `requirements.txt`
- Build context: parent directory (`..`)
- Runs `webapp/app.py` as CMD
- docker-compose.yml: Mounts `../models` as volume for model files
- Optional nginx service for reverse proxy
- Health checks on Flask `/health` endpoint

### Model Details

- **Architecture:** ConvNeXt base (via `timm` library)
- **Input:** RGB images, resized to 224x224, normalized with ImageNet stats
- **Output:** Softmax probabilities over 151 classes (Gen1 Pokemon)
- **Device:** Auto-detects CUDA GPU, falls back to CPU

## Important Notes

- **Package Manager:** Uses UV (not pip)
- **Entry Point:** `poke` CLI defined in `pyproject.toml` → `cli.main:cli`
- **Packages:** `cli`, `webapp`, `lib` all defined in setuptools
- **No Duplicate Code:** All detection logic is in `lib/`, shared by both outputs
- **No Test Suite:** Project currently has no automated tests
- **Dev Dependencies:** Optional (jupyter, ipykernel, jupyterlab) must be added manually to pyproject.toml

## Common Development Tasks

**Adding new dependencies:**
```bash
# Production dependency
uv add package-name

# Dev dependency (manual edit required)
# Edit pyproject.toml [project.optional-dependencies.dev] section
```

**Updating model location:**
- Always use `models/` directory for model files
- Both CLI and webapp check `models/` for weights and class names
- Docker mounts `../models` as volume

**Making changes to core logic:**
- Edit `lib/detector_core.py` - changes apply to both CLI and webapp
- Keep functions pure and well-documented
- Maintain backward compatibility with existing function signatures
