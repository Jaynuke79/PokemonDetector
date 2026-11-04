# Model Files

This directory contains the pre-trained model weights and class names for Pokemon detection.

## Required Files

1. **best_model_fold1.pth** - Pre-trained ConvNeXt model weights (149 Gen1 classes; Nidoran♀ and Nidoran♂ are not among them). Download required.
2. **class_names.json** - JSON list of the 149 class names, in class-index order. Tracked in git.

## Download

Download the weights from Google Drive:
[https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-)

Place the weights next to `class_names.json`:
```
models/
├── best_model_fold1.pth
└── class_names.json
```

## Note

The weights are **not** included in version control due to their size. You must download them manually to use the Pokemon detector.
