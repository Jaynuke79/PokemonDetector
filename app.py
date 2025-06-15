
from flask import Flask, request, render_template, jsonify
import os
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables for model components
class_names = None
model = None
transform = None
device = None

def initialize_model():
    global class_names, model, transform, device
    
    try:
        from scripts.cli.detector import load_class_names, load_model, get_device, get_transform
        
        # Load class names
        class_names_path = "scripts/cli/class_names.json"
        if not os.path.exists(class_names_path):
            print(f"ERROR: Class names file not found at {class_names_path}")
            return False
            
        class_names = load_class_names(class_names_path)
        num_classes = len(class_names)
        device = get_device()
        
        # Check if model file exists locally
        model_path = "scripts/cli/best_model_fold1.pth"
        if not os.path.exists(model_path):
            print(f"ERROR: Model file not found at {model_path}")
            print("Please download the model file from:")
            print("https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing")
            print("And place it in the scripts/cli/ directory")
            return False
        
        # Load the model
        model = load_model("scripts/cli/convnext_base", num_classes, model_path, device)
        if model is None:
            print("ERROR: Failed to load model")
            return False
            
        transform = get_transform()
        
        print("Model initialized successfully!")
        print(f"Device: {device}")
        print(f"Number of classes: {num_classes}")
        return True
        
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        return False

# Initialize the model
print("Initializing Pokemon Detector...")
if not initialize_model():
    print("ERROR: Model initialization failed.")
    print("The app will start but predictions will not work.")
    print("Please ensure:")
    print("1. The model file 'best_model_fold1.pth' is in scripts/cli/")
    print("2. The class_names.json file is in scripts/cli/")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'model_loaded': model is not None})

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded. Please check server logs.'}), 500
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            file.save(tmp_file.name)
            
            try:
                # Real model prediction
                from scripts.cli.detector import predict_image
                results = predict_image(tmp_file.name, model, transform, device, class_names, topk=5)
                
                # Format results
                predictions = []
                for idx, class_name, confidence in results:
                    predictions.append({
                        'class_name': class_name,
                        'confidence': f"{confidence:.4f}",
                        'percentage': f"{confidence * 100:.2f}%"
                    })
                
                return jsonify({'predictions': predictions})
            
            except Exception as e:
                print(f"Prediction error: {str(e)}")
                return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
    
    return jsonify({'error': 'Invalid file type'}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
