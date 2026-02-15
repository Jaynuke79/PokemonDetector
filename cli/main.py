"""
CLI tool for Pokemon detection.

Command-line interface for identifying Pokemon from images using a
pre-trained ConvNeXt model.
"""

import click
from lib.detector_core import (
    load_class_names,
    load_model,
    get_device,
    get_transform,
    predict_image
)


@click.command()
@click.argument("img_path")
@click.option("--topk", default=5, help="Number of top predictions to return.")
@click.option("--model", default="convnext_base", help="Model architecture to use.")
@click.option("--weights", default="models/best_model_fold1.pth", help="Path to model weights file.")
@click.option("--class-names-path", default="models/class_names.json", help="Path to class names JSON file.")
@click.option("--verbose", default=False, help="Enable verbose output.")
def cli(img_path, topk, model, weights, class_names_path, verbose):
    """Command line interface for image classification using a pre-trained model.

    Example usage:
        poke path/to/image.jpg
        poke path/to/image.jpg --topk 3 --verbose true
    """
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
