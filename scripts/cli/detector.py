import numpy as np
import torch
import json
import timm
from torchvision import transforms
from PIL import Image
import click
import os

def load_class_names(path):
    with open(path, "r") as f:
        class_names = json.load(f)
    # print("Class names loaded:", class_names)
    # print("Number of classes:", len(class_names))
    return class_names

def load_model(model_name, num_classes, weight_path, device):
    try:
        model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        model.load_state_dict(torch.load(weight_path, map_location=device))
        model.to(device)
        model.eval()
        # print("Model Loaded")
        return model
    except Exception as e:
        print(e)
        return None

def get_device():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # if device.type == "cuda":
    #     print("GPU in use")
    # else:
    #     print("CPU in use")
    return device

def get_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

def predict_image(img_path, model, transform, device, class_names, topk=2):
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

@click.command()
@click.argument("img_path")
@click.option("--topk", default=5, help="Number of top predictions to return.")
@click.option("--model", default="scripts/cli/convnext_base", help="Model architecture to use.")
@click.option("--weights", default="scripts/cli/best_model_fold1.pth", help="Path to model weights file.")
@click.option("--class-names-path", default="scripts/cli/class_names.json", help="Path to class names JSON file.")
@click.option("--verbose", default=False, help="Enable verbose output.")
def cli(img_path, topk, model, weights, class_names_path, verbose):
    """Command line interface for image classification using a pre-trained model."""
    class_names = load_class_names(class_names_path)
    num_classes = len(class_names)
    device = get_device()
    if verbose:
        print(f"Using device: {device}")
        print(f"Loading model: {model} with {num_classes} classes")
        print(f"Loading weights from: {weights}")
    loaded_model = load_model(model, num_classes, weights, device)
    if loaded_model is None:
        print("Model could not be loaded.")
        return
    transform = get_transform()
    results = predict_image(img_path, loaded_model, transform, device, class_names, topk=topk)
    if verbose:
        print(f"Predictions for image: {img_path}")
    for idx, class_name, confidence in results:
        print(f"Class Index: {idx}, Class Name: {class_name}, Confidence: {confidence:.4f}")

if __name__ == "__main__":
    cli()
