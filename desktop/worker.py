"""
Model loading and classification for the desktop app.

DetectorWorker lives on its own QThread, so loading the model and classifying
images never block the window. Requests queue up and run one at a time.
"""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

MODEL_ARCHITECTURE = "convnext_base"
WEIGHTS_FILENAME = "best_model_fold1.pth"
CLASS_NAMES_FILENAME = "class_names.json"
WEIGHTS_URL = (
    "https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing"
)
TOP_K = 5
# The same formats the web app accepts, by extension and by decoded content.
IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "gif", "bmp")
IMAGE_FORMATS = ("PNG", "JPEG", "GIF", "BMP")
PREVIEW_PIXELS = 768


class DetectorError(Exception):
    def __init__(self, title, message):
        super().__init__(message)
        self.title = title
        self.message = message


def has_image_extension(path):
    return Path(path).suffix.lower().lstrip(".") in IMAGE_EXTENSIONS


def unsupported_file_error(path):
    return DetectorError(
        "Unsupported file",
        f"{Path(path).name} is not a PNG, JPEG, GIF or BMP image.\n\n"
        "Choose a file ending in .png, .jpg, .jpeg, .gif or .bmp.",
    )


def model_file_paths(models_dir):
    """Return the weights and class names paths, or raise if either is missing."""
    weights = models_dir / WEIGHTS_FILENAME
    class_names = models_dir / CLASS_NAMES_FILENAME
    missing = [path for path in (weights, class_names) if not path.is_file()]
    if missing:
        listed = "\n".join(str(path) for path in missing)
        raise DetectorError(
            "Model files are missing",
            f"Pokemon Detector cannot classify images without these files:\n{listed}"
            f"\n\nDownload the model from {WEIGHTS_URL} and place it in {models_dir}, "
            "or reinstall the app.",
        )
    return weights, class_names


def load_preview(path):
    """Decode path as one of IMAGE_FORMATS and return a downscaled QImage of it."""
    with Image.open(path, formats=IMAGE_FORMATS) as image:
        image.thumbnail((PREVIEW_PIXELS, PREVIEW_PIXELS))
        rgba = image.convert("RGBA")
    return QImage(
        rgba.tobytes(), rgba.width, rgba.height, rgba.width * 4, QImage.Format_RGBA8888
    ).copy()


def unreadable_image_error(path):
    return DetectorError(
        "Could not read the image",
        f"{Path(path).name} could not be opened as a PNG, JPEG, GIF or BMP image. "
        "It may be damaged or saved in a different format.",
    )


class DetectorWorker(QObject):
    loaded = Signal(str)
    load_failed = Signal(str, str)
    classified = Signal(str, QImage, list)
    classify_failed = Signal(str, str)

    def __init__(self, models_dir=None):
        super().__init__()
        self._models_dir = models_dir
        self._detector = None
        self._load_error = None

    @Slot()
    def load(self):
        # Importing torch takes seconds, so it happens here, off the UI thread.
        from lib import detector_core

        models_dir = self._models_dir or detector_core.default_models_dir()
        try:
            weights, class_names_path = model_file_paths(models_dir)
            class_names = detector_core.load_class_names(class_names_path)
            device = detector_core.get_device()
            model = detector_core.load_model(
                MODEL_ARCHITECTURE, len(class_names), weights, device
            )
        except DetectorError as error:
            self._load_error = error
        except Exception as error:  # noqa: BLE001
            self._load_error = DetectorError(
                "Could not load the model",
                f"The model in {models_dir} could not be loaded: {error}\n\n"
                "The file may be incomplete. Downloading it again or reinstalling "
                "the app may fix this.",
            )
        else:
            self._detector = (
                detector_core,
                model,
                detector_core.get_transform(),
                device,
                class_names,
            )
            self.loaded.emit(str(device))
            return
        self.load_failed.emit(self._load_error.title, self._load_error.message)

    @Slot(str)
    def classify(self, path):
        if self._detector is None:
            error = self._load_error or DetectorError(
                "The model is not loaded", "The model has not finished loading."
            )
            self.classify_failed.emit(error.title, error.message)
            return
        detector_core, model, transform, device, class_names = self._detector
        try:
            preview = load_preview(path)
            predictions = detector_core.predict_image(
                path,
                model,
                transform,
                device,
                class_names,
                topk=min(TOP_K, len(class_names)),
            )
        except Image.DecompressionBombError:
            self.classify_failed.emit(
                "Image is too large",
                f"{Path(path).name} has too many pixels to classify safely.",
            )
            return
        except (OSError, ValueError):
            error = unreadable_image_error(path)
            self.classify_failed.emit(error.title, error.message)
            return
        except Exception as error:  # noqa: BLE001
            self.classify_failed.emit(
                "Classification failed",
                f"{Path(path).name} could not be classified: {error}",
            )
            return
        self.classified.emit(path, preview, predictions)
