#  Canny Edge Detection GUI

A simple, interactive GUI for creating Canny edge‑detection images with a dark, modern UI.

![](https://raw.githubusercontent.com/jauri1/Canny-Edge-Detection-GUI/refs/heads/main/preview.gif)

## Features

- **Drag & Drop images**  
  Just drag any image into the window to load it.

- **Live Canny settings**  
  Adjust strength and appearance in real time using sliders:
  - Min / Max Canny thresholds
  - Gaussian blur level
  - Brightness and contrast

- **Auto‑copy to clipboard**  
  After you change any setting, the current Canny preview is **automatically copied to the clipboard**, so you can paste it anywhere.

- **Export Canny button**  
  Saves the processed image as `edges_<original_name>` in the same folder as the source file.  
  

## Requirements

- Python 3.8+
- `opencv-python`
- `PySide6`
- `pillow`

## Installation

```bash
pip install opencv-python PySide6 pillow
