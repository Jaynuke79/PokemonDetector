"""
Flask web application for Pokemon detection.

Provides a web interface for uploading images and getting Pokemon predictions.
"""

import contextlib
import os
import tempfile

from flask import Flask, jsonify, render_template, request

# Import core detection functions
from lib.detector_core import (
    default_models_dir,
    get_device,
    get_transform,
    load_class_names,
    load_model,
    predict_image,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Global variables for model components
class_names = None
model = None
transform = None
device = None


def initialize_model():
    """Initialize the Pokemon detection model and related components.

    Returns:
        bool: True if initialization successful, False otherwise
    """
    global class_names, model, transform, device

    try:
        models_dir = default_models_dir()

        class_names_path = models_dir / "class_names.json"
        if not class_names_path.exists():
            print(f"ERROR: Class names file not found: {class_names_path}")
            return False

        class_names = load_class_names(class_names_path)
        num_classes = len(class_names)
        device = get_device()

        model_path = models_dir / "best_model_fold1.pth"
        if not model_path.exists():
            print(f"ERROR: Model file not found: {model_path}")
            print("Please download the model file from:")
            print(
                "https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing"
            )
            print(f"And place it in {models_dir}")
            return False

        # Load the model
        model = load_model("convnext_base", num_classes, model_path, device)
        transform = get_transform()

        print("Model initialized successfully!")
        print(f"Device: {device}")
        print(f"Number of classes: {num_classes}")
        return True

    except Exception as e:  # noqa: BLE001
        print(f"Failed to initialize model: {e}")
        return False


# Initialize the model
print("Initializing Pokemon Detector...")
if not initialize_model():
    print("ERROR: Model initialization failed.")
    print("The app will start but predictions will not work.")
    print("Please ensure:")
    print(f"1. The model file 'best_model_fold1.pth' is in {default_models_dir()}")
    print(f"2. The class_names.json file is in {default_models_dir()}")


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint for monitoring; 503 until the model is loaded."""
    if model is None:
        return jsonify({"status": "unhealthy", "model_loaded": False}), 503
    return jsonify({"status": "healthy", "model_loaded": True})


@app.route("/predict", methods=["POST"])
def predict():
    """Handle prediction requests.

    Expects a multipart/form-data POST with an image file.

    Returns:
        JSON response with predictions or error message
    """
    if model is None:
        return jsonify({"error": "Model not loaded. Please check server logs."}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            file.save(tmp_file.name)

            try:
                # Real model prediction
                results = predict_image(
                    tmp_file.name, model, transform, device, class_names, topk=5
                )

                # Format results
                predictions = []
                for idx, class_name, confidence in results:
                    predictions.append(
                        {
                            "class_name": class_name,
                            "confidence": f"{confidence:.4f}",
                            "percentage": f"{confidence * 100:.2f}%",
                        }
                    )

                return jsonify({"predictions": predictions})

            except Exception as e:  # noqa: BLE001
                print(f"Prediction error: {e!s}")
                return jsonify({"error": f"Prediction failed: {e!s}"}), 500

            finally:
                with contextlib.suppress(OSError):
                    os.unlink(tmp_file.name)

    return jsonify({"error": "Invalid file type"}), 400


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension.

    Args:
        filename: Name of the uploaded file

    Returns:
        bool: True if file extension is allowed
    """
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
