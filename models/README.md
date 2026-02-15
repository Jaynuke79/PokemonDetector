# Models Directory

Place the trained model files here for Docker volume mounting.

## Required Files

Download the pre-trained model from:
https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing

Place the downloaded `best_model_fold1.pth` file in this directory.

This directory is mounted to `/app/scripts/cli` in the Docker container, making the model available to the application.
