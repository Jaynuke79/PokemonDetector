"""
Vercel serverless function for Pokemon detection using OpenRouter API.

This is the backend API that handles image uploads and predictions.
"""

import base64
import json
import math
import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4.5 * 1024 * 1024  # 4.5MB max (Vercel limit)

# OpenRouter configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

ALLOWED_IMAGE_MIME_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/gif", "image/webp"}
)

# All attempts must finish within maxDuration in vercel.json.
OPENROUTER_CONNECT_TIMEOUT_SECONDS = 3
OPENROUTER_READ_TIMEOUT_SECONDS = 25
OPENROUTER_MAX_ATTEMPTS = 2
OPENROUTER_RETRY_DELAY_SECONDS = 1


def parse_error_fallback():
    return [
        {
            "class_name": "Parsing Error - See Console",
            "confidence": "0.0000",
            "percentage": "0.00%",
        }
    ]


def is_valid_base64(value):
    try:
        return bool(base64.b64decode(value, validate=True))
    except ValueError:
        return False


def coerce_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return confidence if math.isfinite(confidence) else 0.0


def format_predictions(data, topk):
    """
    Convert the model's parsed JSON into display-ready predictions.

    Returns an empty list when the reply does not have the expected shape, so
    callers can treat it the same as unparseable JSON.
    """
    if not isinstance(data, dict):
        return []
    predictions = data.get("predictions")
    if not isinstance(predictions, list):
        return []

    formatted_predictions = []
    for pred in [p for p in predictions if isinstance(p, dict)][:topk]:
        confidence = coerce_confidence(pred.get("confidence", 0.0))
        formatted_predictions.append(
            {
                "class_name": str(pred.get("pokemon", "Unknown")),
                "confidence": f"{confidence:.4f}",
                "percentage": f"{confidence * 100:.2f}%",
            }
        )
    return formatted_predictions


def predict_with_openrouter(image_data_base64, mime_type="image/jpeg", topk=5):
    """
    Use OpenRouter API to identify Pokemon in an image.

    Args:
        image_data_base64: Base64 encoded image data
        mime_type: MIME type of the image
        topk: Number of top predictions to return

    Returns:
        List of predictions with class_name and confidence
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    # Prepare the prompt
    prompt = f"""Analyze this image and identify which Pokemon it is. If no pokemon is present, return your best guess.

Return ONLY a JSON object with the top {topk} most likely Pokemon, formatted exactly like this:
{{
  "predictions": [
    {{"pokemon": "PokemonName", "confidence": 0.95}},
    {{"pokemon": "PokemonName", "confidence": 0.03}},
    ...
  ]
}}

Important:
- Use proper Pokemon names (capitalize first letter)
- Confidence scores should sum to approximately 1.0
- Only include Generation 1 Pokemon (Pokemon #1-151)
- Return ONLY the JSON, no other text"""

    # Call OpenRouter API with retry logic
    import time

    for attempt in range(OPENROUTER_MAX_ATTEMPTS):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.environ.get(
                        "VERCEL_URL", "https://pokemon-detector.vercel.app"
                    ),
                    "X-Title": "Pokemon Detector Demo",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data_base64}"
                                    },
                                },
                            ],
                        }
                    ],
                },
                timeout=(
                    OPENROUTER_CONNECT_TIMEOUT_SECONDS,
                    OPENROUTER_READ_TIMEOUT_SECONDS,
                ),
            )

            # Process the response immediately after successful request
            response.raise_for_status()
            result = response.json()

            # Extract the response text
            if "choices" not in result or len(result["choices"]) == 0:
                openrouter_error = result.get("error", result)
                raise ValueError(
                    f"No choices in OpenRouter response: {openrouter_error}"
                )

            response_text = result["choices"][0]["message"]["content"]
            if not isinstance(response_text, str):
                print(f"OpenRouter returned non-text content: {response_text!r}")
                return parse_error_fallback()

            # Parse the JSON response
            try:
                # Sometimes the model wraps JSON in markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Failed to parse OpenRouter response: {e}")
                print(f"Raw response: {response_text}")
                return parse_error_fallback()

            formatted_predictions = format_predictions(data, topk)
            if not formatted_predictions:
                print("OpenRouter response has no usable predictions")
                print(f"Raw response: {response_text}")
                return parse_error_fallback()

            return formatted_predictions

        except requests.exceptions.Timeout:
            if attempt < OPENROUTER_MAX_ATTEMPTS - 1:
                print(f"Timeout on attempt {attempt + 1}, retrying...")
                time.sleep(OPENROUTER_RETRY_DELAY_SECONDS)
                continue
            else:
                # Final attempt failed - raise helpful error
                raise ValueError(
                    f"OpenRouter API timed out after {OPENROUTER_MAX_ATTEMPTS} attempts. "
                    f"The model '{OPENROUTER_MODEL}' did not respond within "
                    f"{OPENROUTER_READ_TIMEOUT_SECONDS}s per attempt. "
                    "Try a faster model like 'anthropic/claude-3-haiku' "
                    "or a smaller image."
                )

        except requests.exceptions.RequestException as e:
            # Other request errors (connection, HTTP errors, etc.)
            print(f"OpenRouter API error on attempt {attempt + 1}: {e}")
            if attempt < OPENROUTER_MAX_ATTEMPTS - 1:
                time.sleep(OPENROUTER_RETRY_DELAY_SECONDS)
                continue
            else:
                raise


@app.route("/")
@app.route("/api")
def root():
    """Root endpoint - confirms API is working."""
    return jsonify(
        {
            "message": "Pokemon Detector API is running",
            "endpoints": {"health": "/api/health", "predict": "/api/predict (POST)"},
        }
    )


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    api_key_set = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
    return jsonify(
        {"status": "healthy", "api_configured": api_key_set, "model": OPENROUTER_MODEL}
    )


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Handle prediction requests.

    Expects JSON with base64 encoded image.
    Returns JSON response with predictions.
    """
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "OpenRouter API key not configured"}), 500

    try:
        # Get JSON data
        data = request.get_json()

        if not data or "image" not in data:
            return jsonify({"error": "No image data provided"}), 400

        # Extract base64 image data
        image_data = data["image"].strip()

        # Handle data URL format (data:image/png;base64,...)
        if image_data[:5].lower() == "data:":
            # Extract MIME type and base64 data
            header, separator, encoded = image_data.partition(",")
            mime_type = header.split(":")[1].split(";")[0].strip().lower()
            if not separator or mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                allowed_types = ", ".join(sorted(ALLOWED_IMAGE_MIME_TYPES))
                return jsonify(
                    {"error": f"Unsupported image type. Allowed: {allowed_types}"}
                ), 400
            image_base64 = encoded
        else:
            # Assume it's just base64 data
            mime_type = "image/jpeg"
            image_base64 = image_data

        if not is_valid_base64(image_base64):
            return jsonify({"error": "Image data is not valid base64"}), 400

        # Get predictions from OpenRouter
        predictions = predict_with_openrouter(image_base64, mime_type, topk=5)
        return jsonify({"predictions": predictions})

    except Exception as e:  # noqa: BLE001
        print(f"Prediction error: {e!s}")
        return jsonify({"error": f"Prediction failed: {e!s}"}), 500


# Vercel needs the app to be exported
# The Flask app object itself is the handler
# No need for a wrapper function

# For local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
