# PokemonDetector

A Pokemon detection system using a PyTorch-based ConvNeXt model to identify Pokemon from images.

Originally built as a class project, this repository demonstrates modern project development and management practices with clearly separated outputs.

---

## 📦 Project Outputs

This project contains 4 outputs: a linux cli tool, a windows installer, a local docker web-app, and an online vercel demo.

1. **Linux CLI Tool** (`poke` command) - Command-line interface for quick predictions
2. **Windows Installer** - Installs the CLI and the web app (see [Windows Installer](#-windows-installer))
3. **Docker Web Application** - Flask-based web interface with image upload, run locally in a Docker container
4. **Vercel Demo** - Online demo hosted on Vercel (see [demo-vercel/](demo-vercel/))

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
│   └── templates/         # HTML templates
│
├── lib/                   # Shared Core Library
│   ├── __init__.py
│   └── detector_core.py   # Model loading & prediction logic
│
├── deployment/            # Docker Deployment Method
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.direct.yml  # Publishes the app without nginx
│   └── nginx.config
│
├── models/                # Model Files (see models/README.md)
│   ├── best_model_fold1.pth      # Download required
│   └── class_names.json          # Included in the repository
│
├── windows/               # Windows Executable and Installer Build
│
├── demo-vercel/           # Vercel Demo (deployed on its own)
│
├── tests/                 # Test Suite
│
├── requirements.txt       # Pinned dependencies for the Docker image and Windows build
├── pyproject.toml         # Project configuration
├── LICENSE                # GNU AGPL v3
├── NOTICE                 # Copyright notice
└── THIRD_PARTY_NOTICES.md # Licenses of the components the Windows installer bundles
```

---

## 🚀 Quick Start

### Prerequisites

1. **Install UV** (Python package manager) - See the [installation guide](https://docs.astral.sh/uv/getting-started/installation/). The project requires Python 3.10 or newer
2. **Download the Model Weights** - Save `best_model_fold1.pth` from [Google Drive](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing) into `models/`. See also [models/README.md](models/README.md)

### Setup

```bash
# Clone the repository
git clone https://github.com/Jaynuke79/PokemonDetector.git
cd PokemonDetector

# Install dependencies
uv sync

# Optional: activate the environment (uv run does not need this)
source .venv/bin/activate
```

---

## 🎯 Using the Outputs

### 1. CLI Tool

```bash
# Basic prediction
uv run poke path/to/image.jpg

# Top 3 predictions with verbose output
uv run poke path/to/image.jpg --topk 3 --verbose

# Custom model weights
uv run poke path/to/image.jpg --weights models/best_model_fold1.pth --class-names-path models/class_names.json
```

Example, using the image in the repository:

```console
$ uv run poke gengar.png --topk 3
Class Index: 40, Class Name: Gengar, Confidence: 0.9984
Class Index: 51, Class Name: Haunter, Confidence: 0.0011
Class Index: 114, Class Name: Rhydon, Confidence: 0.0001
```

| Option | Default | Description |
|---|---|---|
| `--topk` | 5 | Number of predictions, from 1 up to the number of classes |
| `--model` | `convnext_base` | Model architecture |
| `--weights` | `best_model_fold1.pth` in the models directory | Path to the weights file |
| `--class-names-path` | `class_names.json` in the models directory | Path to the class names file |
| `--verbose` | off | Flag that prints the device, model and weights being used |

The command exits with 0 on success, 2 for invalid arguments or a missing file, and 1 if the model fails to load (with the cause on stderr) or the input file can't be read as an image (with a traceback).

### 2. Web Application (Local)

```bash
# Run Flask app
uv run python -m webapp.app

# Access at http://localhost:5000
```

`python webapp/app.py` only works when the package is installed, for example by `uv sync`, because it puts `webapp/` rather than the repo root on `sys.path`. `python -m webapp.app` from the repo root works either way.

Upload an image through the web interface to get top 5 predictions. Uploads must be a PNG, JPEG, GIF or BMP image of at most 16 MB and 50 million pixels, with a `.png`, `.jpg`, `.jpeg`, `.gif` or `.bmp` filename.

Without the model files the app still starts, but `/health` returns 503 and `/predict` returns 500. With them, `/health` returns 200.

### 3. Docker Deployment

```bash
# Navigate to deployment directory
cd deployment

# Build and run the app behind nginx
docker compose up --build

# Access at http://localhost (port 80)

# Or run only the app, without nginx
docker compose -f docker-compose.yml -f docker-compose.direct.yml up --build pokemon-detector

# Access at http://localhost:5000

# Stop services
docker compose down
```

The image uses Python 3.11 and CPU-only PyTorch, and serves the app with gunicorn. Compose mounts `models/` into the container, so download the weights first. Until they are there the container reports unhealthy, and because the model only loads at startup, restart it after adding them.

### 4. Vercel Demo

The demo runs from [demo-vercel/](demo-vercel/) on its own, without PyTorch or the trained model. It sends images to a vision model through the OpenRouter API, so it needs an `OPENROUTER_API_KEY`; `OPENROUTER_MODEL` selects the model. Uploads must be a PNG, JPEG, GIF or WebP image of about 3.3 MB or less, because the 4.5 MB request limit applies to the base64-encoded image.

See [demo-vercel/README.md](demo-vercel/README.md) to deploy it and [demo-vercel/TROUBLESHOOTING.md](demo-vercel/TROUBLESHOOTING.md) for common problems.

---

## 🧪 Running Tests

```bash
uv sync --extra test
.venv/bin/pytest
```

The tests use a stub model and never load the real weights, so they don't need the download.

---

## 🏗️ Architecture

The CLI, web application and Windows installer share the same core detection logic from `lib/detector_core.py`:

- **Model**: ConvNeXt base architecture (via `timm` library)
- **Input**: Images resized to 224x224, normalized with ImageNet stats
- **Output**: Top-k predictions with confidence scores
- **Classes**: 149 Generation 1 Pokemon, listed in `models/class_names.json`

**Shared Library (`lib/detector_core.py`):**
- `default_models_dir()` - Locate the model files
- `load_class_names()` - Load Pokemon class labels
- `load_model()` - Initialize ConvNeXt model with weights
- `get_device()` - Detect CUDA/CPU
- `get_transform()` - Image preprocessing pipeline
- `predict_image()` - Run inference and return top-k results

**CLI Tool** imports the library and provides a Click-based command interface.

**Web Application** imports the library and wraps it in Flask routes with HTML upload form: `/`, `/predict` and `/health`.

**Docker Deployment** containerizes the web application with volume mounts for model files. nginx is the published entry point on port 80 and has no TLS; `docker-compose.direct.yml` publishes the app on `127.0.0.1:5000` instead.

**Vercel Demo** does not use the library. It keeps its own copy of the results rendering and prediction formatting, and tests check that the copies match.

---

## 📝 Technologies

- **UV** - Python package management
- **PyTorch** - Deep learning framework
- **TIMM** - Pre-trained model library
- **Click** - CLI framework
- **Flask** - Web framework
- **Gunicorn** - WSGI server in the Docker image
- **nginx** - Reverse proxy in the Docker deployment
- **Docker** - Containerization
- **OpenRouter** - Vision model API for the Vercel demo
- **pytest** - Test framework

---

## ⚠️ Important Notes

- The model weights (`best_model_fold1.pth`) are **not** in version control; `class_names.json` is
- Download the weights from [Google Drive](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing)
- Place the file in the `models/` directory
- To keep the model files elsewhere, point the CLI and web app at that directory with the `POKE_MODELS_DIR` environment variable
- The CLI and web app look in `POKE_MODELS_DIR`, then the Windows install's bundle, then `models/` in the project root. A `models/` in the current directory is not used
- After a non-editable install such as `pip install .`, the project root has no models, so set `POKE_MODELS_DIR` or pass `--weights` and `--class-names-path`
- The model is trained on 149 Generation 1 Pokemon. Nidoran♀ and Nidoran♂ are not among its classes

---

## 💻 Windows Installer

`PokemonDetectorSetup-<version>.exe` installs the CLI and the web app on Windows 10 or later (64-bit). Python is not required, and neither are administrator rights.

### Getting the Installer

GitHub Actions builds the installer. Open a successful [Windows installer run](https://github.com/Jaynuke79/PokemonDetector/actions/workflows/windows-installer.yml) while signed in to GitHub and download the `PokemonDetectorSetup` artifact, which holds the installer and its SHA-256. Artifacts expire after 7 days, and you can start a new run with "Run workflow". There is no published release yet.

The installer isn't code signed, so Windows SmartScreen warns about it. Choose "More info", then "Run anyway".

### What It Installs

- **Location**: `%LOCALAPPDATA%\Programs\PokemonDetector` by default, for the current user only
- **Pokemon Detector** in the Start Menu: starts the web app on `127.0.0.1` and opens it in your browser. It uses port 5000, or another free port if that one is taken. Close its console window to stop it
- **Pokemon Detector CLI** in the Start Menu: opens a console where you can run `poke your_image.png`
- **PATH** (optional, on by default): lets `poke` run from any new terminal. Uninstalling removes the entry
- **Desktop icon** (optional, off by default)
- The model weights and class names, so nothing else needs downloading
- `LICENSE`, `NOTICE` and `THIRD_PARTY_NOTICES.md` in the install folder. Setup shows the license first, and you must accept it to install

The web app takes a moment to start and every `poke` run takes a moment, because the model has to load.

### What Has Been Tested

The workflow runs the real installer on a GitHub-hosted Windows runner: silent install, `poke` from another directory through the PATH, a `gengar.png` upload to the web app, an upgrade over the top and a silent uninstall. Setup and the uninstaller refuse to run while the web app is open. The workflow builds with `windows\build_windows.bat`, so that script's success path runs too, but not its error messages. The wizard's pages, including the license page, and the browser opening can't be exercised on a headless runner, and the runner isn't a machine without developer tools.

### Building It Yourself

Download the model weights into `models/` first, because the build bundles them. Then, on Windows with Python 3.11:

```batch
windows\build_windows.bat
```

This creates `windows\dist\PokemonDetector\` and, if [Inno Setup 6](https://jrsoftware.org/isinfo.php) is installed, the installer in `windows\installer_output\`. See [windows/DISTRIBUTION_PACKAGE.md](windows/DISTRIBUTION_PACKAGE.md).

---

## 📄 License

Copyright (C) 2025-2026 Jayden Alonzo-Estrada

The code is licensed under the [GNU Affero General Public License v3.0](LICENSE) (`AGPL-3.0-only`). You may use, modify and share it under that license; if you run a modified version as a network service, you must offer its users the source code of that version.

The license covers this repository's code. It does not cover the images the model weights were trained on. Pokémon names are trademarks of Nintendo, Game Freak and Creatures. The Windows installer bundles third-party components under their own licenses, listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

Feel free to explore the directories and contribute!
