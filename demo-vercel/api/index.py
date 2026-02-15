"""
Vercel serverless function for Pokemon detection using OpenRouter API.

This is the backend API that handles image uploads and predictions.
"""

from flask import Flask, request, jsonify
import os
import base64
import requests
import tempfile
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4.5 * 1024 * 1024  # 4.5MB max (Vercel limit)

# OpenRouter configuration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')


def predict_with_openrouter(image_data_base64, mime_type='image/jpeg', topk=5):
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

    # Call OpenRouter API
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get('VERCEL_URL', 'https://pokemon-detector.vercel.app'),
                "X-Title": "Pokemon Detector Demo"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data_base64}"
                                }
                            }
                        ]
                    }
                ]
            },
            timeout=10  # Vercel has 10s limit for Hobby tier, 25s for Pro
        )

        response.raise_for_status()
        result = response.json()

        # Extract the response text
        if 'choices' not in result or len(result['choices']) == 0:
            raise ValueError("No response from OpenRouter API")

        response_text = result['choices'][0]['message']['content']

        # Parse the JSON response
        try:
            # Sometimes the model wraps JSON in markdown code blocks
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            data = json.loads(response_text)
            predictions = data.get('predictions', [])

            # Format predictions
            formatted_predictions = []
            for pred in predictions[:topk]:
                formatted_predictions.append({
                    'class_name': pred.get('pokemon', 'Unknown'),
                    'confidence': f"{pred.get('confidence', 0.0):.4f}",
                    'percentage': f"{pred.get('confidence', 0.0) * 100:.2f}%"
                })

            return formatted_predictions

        except json.JSONDecodeError as e:
            # If parsing fails, return a fallback response
            print(f"Failed to parse OpenRouter response: {e}")
            print(f"Raw response: {response_text}")
            return [{
                'class_name': 'Parsing Error - See Console',
                'confidence': '0.0000',
                'percentage': '0.00%'
            }]

    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API error: {e}")
        raise


@app.route('/')
@app.route('/api')
def root():
    """Root endpoint - confirms API is working."""
    return jsonify({
        'message': 'Pokemon Detector API is running',
        'endpoints': {
            'health': '/api/health',
            'predict': '/api/predict (POST)'
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    api_key_set = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
    return jsonify({
        'status': 'healthy',
        'api_configured': api_key_set,
        'model': OPENROUTER_MODEL
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Handle prediction requests.

    Expects JSON with base64 encoded image.
    Returns JSON response with predictions.
    """
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'OpenRouter API key not configured'}), 500

    try:
        # Get JSON data
        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Extract base64 image data
        image_data = data['image']

        # Handle data URL format (data:image/png;base64,...)
        if image_data.startswith('data:'):
            # Extract MIME type and base64 data
            header, encoded = image_data.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
            image_base64 = encoded
        else:
            # Assume it's just base64 data
            mime_type = 'image/jpeg'
            image_base64 = image_data

        # Get predictions from OpenRouter
        predictions = predict_with_openrouter(image_base64, mime_type, topk=5)
        return jsonify({'predictions': predictions})

    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


# Vercel needs the app to be exported
# The Flask app object itself is the handler
# No need for a wrapper function

# For local testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
