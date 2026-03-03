# Model Files

This directory contains the pre-trained model weights and class names for Pokemon detection.

## Required Files

1. **best_model_fold1.pth** - Pre-trained ConvNeXt model weights (151 Pokemon classes, Gen1)
2. **class_names.json** - JSON file mapping class indices to Pokemon names

## Download

Download the model file from Google Drive:
[https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-)

Place both files in this directory:
```
models/
├── best_model_fold1.pth
└── class_names.json
```

## Note

These files are **not** included in version control due to their size. You must download them manually to use the Pokemon detector.
