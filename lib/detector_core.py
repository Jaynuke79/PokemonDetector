"""
Core Pokemon detection library.

This module contains shared logic for loading models and making predictions,
used by both the CLI tool and web application.
"""

import numpy as np
import torch
import json
import timm
from torchvision import transforms
from PIL import Image
import os


def load_class_names(path):
    """Load class names from a JSON file.

    Args:
        path: Path to the JSON file containing class names

    Returns:
        List of class names
    """
    with open(path, "r") as f:
        class_names = json.load(f)
    return class_names


def load_model(model_name, num_classes, weight_path, device):
    """Load a pre-trained model with weights.

    Args:
        model_name: Name of the timm model architecture (e.g., 'convnext_base')
        num_classes: Number of output classes
        weight_path: Path to the model weights file
        device: PyTorch device (cpu or cuda)

    Returns:
        Loaded model in eval mode, or None if loading failed
    """
    try:
        model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        model.load_state_dict(torch.load(weight_path, map_location=device))
        model.to(device)
        model.eval()
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def get_device():
    """Get the appropriate PyTorch device (CUDA if available, else CPU).

    Returns:
        PyTorch device object
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return device


def get_transform():
    """Get the image transformation pipeline for the model.

    Returns:
        torchvision.transforms.Compose object with the required transformations
    """
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])


def predict_image(img_path, model, transform, device, class_names, topk=2):
    """Make predictions on an image.

    Args:
        img_path: Path to the image file
        model: Loaded PyTorch model
        transform: Image transformation pipeline
        device: PyTorch device
        class_names: List of class names
        topk: Number of top predictions to return

    Returns:
        List of tuples (class_index, class_name, confidence)
    """
    image = Image.open(img_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)
    model.eval()
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = torch.softmax(output, dim=1)[0]
        topk_results = torch.topk(probabilities, topk)
        results = []
        for idx, conf in zip(topk_results.indices, topk_results.values):
            results.append((idx.item(), class_names[idx.item()], conf.item()))
    return results
