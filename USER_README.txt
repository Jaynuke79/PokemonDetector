===========================================
  Pokemon Detector - Windows Edition
===========================================

Thank you for using Pokemon Detector!
This tool uses AI to identify Pokemon from images.

===========================================
  QUICK START
===========================================

METHOD 1: Drag and Drop (Easiest!)
-----------------------------------
1. Drag any Pokemon image onto "drop_image_here.bat"
2. Wait for results
3. Press any key to close

METHOD 2: Command Line
----------------------
1. Open Command Prompt in this folder
   (Shift + Right-click in folder -> "Open PowerShell window here")
2. Type: poke.exe your_image.png
3. Press Enter

===========================================
  EXAMPLES
===========================================

# Basic usage
poke.exe gengar.png

# Show top 10 predictions instead of 5
poke.exe gengar.png --topk 10

# Enable detailed output
poke.exe gengar.png --verbose True

# Analyze image from another location
poke.exe C:\Users\YourName\Pictures\pikachu.jpg

# Get help and see all options
poke.exe --help

===========================================
  SUPPORTED IMAGE FORMATS
===========================================

- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- GIF (.gif)

===========================================
  CURRENT LIMITATIONS
===========================================

- Trained on Generation 1 Pokemon only (151 original Pokemon)
- Works best with clear images showing the Pokemon
- May not work well with:
  * Multiple Pokemon in one image
  * Heavily edited or stylized fan art
  * Very low quality or blurry images

===========================================
  TROUBLESHOOTING
===========================================

Problem: "Missing DLL" error
Solution: Install Microsoft Visual C++ Redistributable:
          https://aka.ms/vs/17/release/vc_redist.x64.exe

Problem: Program is slow
Solution: First run is always slower (10-30 seconds).
          Subsequent runs are faster.

Problem: Wrong predictions
Solution: Try a clearer image or different angle.
          The model works best with official Pokemon artwork.

Problem: Program won't start
Solution: Make sure you're on Windows 10 or later.
          Try running as Administrator (right-click -> Run as Administrator).

===========================================
  ABOUT
===========================================

Pokemon Detector uses:
- Deep Learning (PyTorch)
- ConvNeXt neural network architecture
- Transfer learning on Pokemon dataset

This is a class project demonstrating:
- Machine Learning deployment
- Software packaging
- Cross-platform distribution

Generation 1 Pokemon (151 species) are currently supported.

===========================================
  TECHNICAL DETAILS
===========================================

Model: ConvNeXt Base
Training: Transfer learning on Gen 1 Pokemon dataset
Inference: CPU-based (works on any Windows PC)
Dependencies: Bundled (PyTorch, NumPy, Pillow)
Size: ~500MB-1GB (all-in-one executable)

===========================================
  MORE INFORMATION
===========================================

GitHub Repository:
https://github.com/Jaynuke79/PokemonDetector

Report Issues:
https://github.com/Jaynuke79/PokemonDetector/issues

Want to train on more generations?
Check the repository for training scripts!

===========================================

Built with PyTorch and PyInstaller
© 2025 - Educational Project

===========================================
