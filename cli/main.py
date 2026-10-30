"""
CLI tool for Pokemon detection.

Command-line interface for identifying Pokemon from images using a
pre-trained ConvNeXt model.
"""

import click

from lib.detector_core import (
    default_models_dir,
    get_device,
    get_transform,
    load_class_names,
    load_model,
    predict_image,
)

EXISTING_FILE = click.Path(exists=True, dir_okay=False)


def _default_model_file(filename):
    return lambda: str(default_models_dir() / filename)


@click.command()
@click.argument("img_path", type=EXISTING_FILE)
@click.option(
    "--topk",
    default=5,
    type=click.IntRange(min=1),
    help="Number of top predictions to return.",
)
@click.option("--model", default="convnext_base", help="Model architecture to use.")
@click.option(
    "--weights",
    default=_default_model_file("best_model_fold1.pth"),
    type=EXISTING_FILE,
    help="Path to model weights file.",
)
@click.option(
    "--class-names-path",
    default=_default_model_file("class_names.json"),
    type=EXISTING_FILE,
    help="Path to class names JSON file.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
def cli(img_path, topk, model, weights, class_names_path, verbose):
    """Command line interface for image classification using a pre-trained model.

    Example usage:
        poke path/to/image.jpg
        poke path/to/image.jpg --topk 3 --verbose
    """
    class_names = load_class_names(class_names_path)
    num_classes = len(class_names)
    if topk > num_classes:
        raise click.BadParameter(
            f"{topk} exceeds the {num_classes} available classes.",
            param_hint="--topk",
        )

    device = get_device()

    if verbose:
        print(f"Using device: {device}")
        print(f"Loading model: {model} with {num_classes} classes")
        print(f"Loading weights from: {weights}")

    try:
        loaded_model = load_model(model, num_classes, weights, device)
    except Exception as e:
        raise click.ClickException(f"Could not load model: {e}") from e

    transform = get_transform()
    results = predict_image(
        img_path, loaded_model, transform, device, class_names, topk=topk
    )

    if verbose:
        print(f"Predictions for image: {img_path}")

    for idx, class_name, confidence in results:
        print(
            f"Class Index: {idx}, Class Name: {class_name}, Confidence: {confidence:.4f}"
        )


if __name__ == "__main__":
    cli()
