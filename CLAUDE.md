# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PokemonDetector is a web application that uses a PyTorch-based ConvNeXt model to identify Pokemon from images. The project supports both CLI and web-based prediction interfaces.

## Development Commands

### Environment Setup
```bash
# Activate UV virtual environment
source .venv/bin/activate

# Install dependencies (if needed)
uv sync
```

### Running the Application

**CLI Interface:**
```bash
# Basic prediction
uv run poke <img_path>

# With custom options
uv run poke <img_path> --topk 5 --verbose true

# Custom model/weights
uv run poke <img_path> --model scripts/cli/convnext_base --weights scripts/cli/best_model_fold1.pth --class-names-path scripts/cli/class_names.json
```

**Web Application:**
```bash
# Run Flask app locally
python app.py

# Access at http://localhost:5000
```

**Docker:**
```bash
# Build and run with docker compose (V2)
docker compose up --build

# Run only app service (without nginx)
docker compose up pokemon-detector

# Stop services
docker compose down

# Web app: http://localhost:5000
# Nginx (if enabled): http://localhost:80
```

## Architecture

### Model Requirements

The application requires two critical files:
- `best_model_fold1.pth` - Pre-trained ConvNeXt model weights (must be downloaded from [Google Drive](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing))
- `class_names.json` - Pokemon class labels (151 classes for Gen1)

**File Locations:**
- For local development: place in `scripts/cli/`
- For Docker: place in `models/` directory (mounted as volume)

**Note:** The model file is NOT in version control. The app will start without it but predictions will fail with informative errors.

### Core Components

**Detection Logic:**
- `scripts/cli/detector.py` - Shared model loading, prediction, and CLI interface
- `app/detector.py` - Earlier version of detector logic (deprecated but present)
- Model uses `timm` library with ConvNeXt architecture
- Images are resized to 224x224 and normalized with ImageNet stats
- Returns top-k predictions with confidence scores

**Web Application:**
- `app.py` - Flask server, handles file uploads and prediction routing
- Loads model globally on startup from `scripts/cli/detector.py`
- `/predict` endpoint accepts image uploads (max 16MB)
- `/health` endpoint for container health checks
- Returns JSON with top 5 predictions by default

**Dual Code Paths:**
Both `app/detector.py` and `scripts/cli/detector.py` contain similar prediction logic, but `scripts/cli/detector.py` is the canonical version used by both CLI and web app. The `app/` module appears to be an earlier implementation.

### Docker Configuration

- Dockerfile uses Python 3.10-slim base image
- Model weights mounted as volume: `./models:/app/models`
- App checks both `models/` (Docker) and `scripts/cli/` (local) for model files
- Optional nginx reverse proxy configuration included
- Health checks verify Flask server is responding

## Project Structure Notes

- Uses UV for Python package management (not pip)
- Project configured as installable package with `poke` CLI script
- Frontend templates are in `templates/` (basic HTML upload form)
- No test suite present
- Dev dependencies (jupyter, notebook) are optional and must be added manually to pyproject.toml
