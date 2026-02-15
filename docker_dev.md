# Docker Development Documentation

This document tracks changes made to enable Docker deployment for the PokemonDetector application.

## Overview

The Docker configuration was initially non-functional due to several missing files and configuration issues. This document details the problems encountered, changes made, and their effects.

---

## Initial Problems

### 1. Missing `requirements.txt`
**Problem:**
- Dockerfile (line 16-17) attempted to copy and install from `requirements.txt`
- File did not exist because project uses UV package manager with `pyproject.toml`

**Solution:**
```bash
uv pip compile pyproject.toml -o requirements.txt
```

**Effect:**
- Generated `requirements.txt` with all 57 dependencies (Flask, PyTorch, timm, etc.)
- Allows Docker to install Python dependencies without UV
- File contains pinned versions for reproducible builds

---

### 2. Incorrect nginx Configuration Filename
**Problem:**
- `docker-compose.yml` line 32 referenced `nginx.conf`
- Actual file is named `nginx.config`
- Would cause nginx service to fail on startup

**Solution:**
Changed in `docker-compose.yml`:
```yaml
# Before:
- "./nginx.conf:/etc/nginx/nginx.conf:ro"

# After:
- "./nginx.config:/etc/nginx/nginx.conf:ro"
```

**Effect:**
- nginx service can now properly mount its configuration file
- Prevents container startup failure

---

### 3. Missing Volume Mount Directories
**Problem:**
- `docker-compose.yml` attempted to mount `./models` and `./uploads` directories
- Directories did not exist in repository
- Model file (`best_model_fold1.pth`) had no designated location

**Solution:**
```bash
mkdir -p models uploads
cp data/class_names.json models/
```

Created `models/README.md` with download instructions for the model file.

**Effect:**
- Provides clear location for model files (`models/`)
- Docker volume mounts succeed
- Users have clear instructions on where to place downloaded model

---

### 4. Volume Mount Overwriting Application Code (Critical Issue)
**Problem:**
- Original `docker-compose.yml` line 8: `- "./models:/app/scripts/cli"`
- This mount **replaced** the entire `scripts/cli/` directory inside the container
- `scripts/cli/detector.py` (required Python code) was removed by the mount
- Only model files from host were present, no Python code
- App failed with "Model not loaded" error

**Solution:**
Changed volume mount path in `docker-compose.yml`:
```yaml
# Before:
- "./models:/app/scripts/cli"

# After:
- "./models:/app/models"
```

Updated `app.py` to check both locations:
```python
# Before:
class_names_path = "scripts/cli/class_names.json"
model_path = "scripts/cli/best_model_fold1.pth"

# After:
class_names_paths = ["models/class_names.json", "scripts/cli/class_names.json"]
model_paths = ["models/best_model_fold1.pth", "scripts/cli/best_model_fold1.pth"]
# Checks both locations, uses first found
```

Updated `Dockerfile` line 23:
```dockerfile
RUN mkdir -p scripts/cli templates static models uploads
```

**Effect:**
- Application code in `scripts/cli/` is preserved in container
- Model files mounted separately to `/app/models`
- App works in both Docker (uses `models/`) and local dev (uses `scripts/cli/`)
- Single codebase supports both deployment methods

---

## File Changes Summary

### Created Files
1. **`requirements.txt`** - Python dependencies for Docker installation
2. **`models/README.md`** - Instructions for downloading model files
3. **`models/class_names.json`** - Pokemon class labels (copied from `data/`)
4. **`CLAUDE.md`** - Development guide for Claude Code
5. **`docker_dev.md`** - This file

### Modified Files
1. **`docker-compose.yml`**
   - Line 8: Changed mount from `./models:/app/scripts/cli` to `./models:/app/models`
   - Line 32: Changed `nginx.conf` to `nginx.config`

2. **`app.py`**
   - Lines 22-42: Added dual-path checking for model/class_names files
   - Changed model architecture name from `"scripts/cli/convnext_base"` to `"convnext_base"`
   - Now supports both Docker (`models/`) and local (`scripts/cli/`) environments

3. **`Dockerfile`**
   - Line 23: Added `models` and `uploads` to directory creation

4. **`CLAUDE.md`**
   - Updated to reflect correct Docker Compose V2 syntax (`docker compose` not `docker-compose`)
   - Updated model file location documentation
   - Updated Docker configuration notes

---

## Docker Architecture

### Directory Structure (Host)
```
pokemonDetector/
├── models/                      # Model files for Docker
│   ├── best_model_fold1.pth    # Downloaded model (335MB)
│   ├── class_names.json        # Pokemon labels
│   └── README.md               # Download instructions
├── scripts/cli/                 # Application code
│   ├── detector.py             # Model loading logic
│   └── class_names.json        # Pokemon labels (local dev)
├── uploads/                     # Persistent uploads
├── docker-compose.yml
└── Dockerfile
```

### Directory Structure (Container)
```
/app/
├── models/                      # Volume mount from ./models
│   ├── best_model_fold1.pth
│   └── class_names.json
├── scripts/cli/                 # From COPY . . in Dockerfile
│   ├── detector.py             # Preserved!
│   └── class_names.json
├── uploads/                     # Volume mount from ./uploads
├── templates/
├── static/
├── app.py
└── requirements.txt
```

### Key Design Decision
The application uses **fallback path checking** to work in multiple environments:
- **Docker:** Checks `models/` first (volume mounted)
- **Local:** Falls back to `scripts/cli/` (standard dev location)
- **Benefit:** Same code runs in both environments without modification

---

## Running Docker

### Prerequisites
```bash
# 1. Download model file
# From: https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
# Save to: ./models/best_model_fold1.pth

# 2. Ensure class_names.json is in models/
ls models/class_names.json
```

### Build and Run
```bash
# Full stack (app + nginx)
docker compose up --build

# App only (no nginx)
docker compose up pokemon-detector

# Detached mode
docker compose up -d

# Stop all services
docker compose down
```

### Access Points
- Web app: http://localhost:5000
- Nginx (if enabled): http://localhost:80
- Health check: http://localhost:5000/health

---

## Testing Checklist

After rebuilding, verify:

- [ ] Container builds without errors
- [ ] App starts and loads model successfully
- [ ] Health check returns `{"status": "healthy", "model_loaded": true}`
- [ ] Web UI loads at http://localhost:5000
- [ ] Image upload and prediction works
- [ ] Predictions return top 5 Pokemon with confidence scores

---

## Troubleshooting

### "Model not loaded" Error
**Cause:** Model file not found in expected locations

**Check:**
```bash
# Verify model exists on host
ls -lh models/best_model_fold1.pth

# Check container logs
docker compose logs pokemon-detector
```

**Expected log output:**
```
Model initialized successfully!
Device: cuda/cpu
Number of classes: 151
```

### Container Fails to Start
**Check:**
```bash
# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up
```

### Permission Issues
Docker volumes inherit host file permissions. If encountering permission errors:
```bash
# Ensure proper ownership
chmod 644 models/*.pth models/*.json
```

---

## Future Improvements

1. **Multi-stage Docker build** - Reduce final image size
2. **Environment variables** - Make paths configurable
3. **Model download script** - Automate model acquisition
4. **Health check enhancement** - Verify model prediction capability
5. **Production optimizations** - Gunicorn/uWSGI instead of Flask dev server
