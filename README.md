# Yiyu's Toolbox (乙羽的工具箱)

[中文文档](README_CN.md)

A local, offline AI-powered watermark removal tool based on the LaMa (Large Mask Inpainting) model. 

This project is a refactor and enhancement of the "AI Magic Eraser" (AI魔法消除小工具) originally by **zhaoyun007** from 52pojie.cn.

## Features

- **Offline AI Inpainting**: Uses the LaMa model for high-quality object and watermark removal without internet access.
- **Interactive UI**:
    - **Brush Tool**: Customizable brush size for precise masking.
    - **Zoom & Pan**: Mouse wheel to zoom, Middle Click (or Right Click) to pan the image.
    - **Quick Undo**: Right-click to instantly clear the current mask.
- **Batch Processing**: 
    - efficiently process multiple images with the same watermark position.
    - **Workflow**: Load one image -> Draw Mask -> Click 'Batch Process' -> Select Folder.
- **Video Auto Shot Splitter**:
    - **Batch Processing**: Supports batch processing of all videos in a folder.
    - **Multiple Modes**: Extract start, middle, or end frames, or automatically split into 20 evenly distributed snapshots.
    - **Smart Saving**: Automatically categorizes and saves snapshots and video files.
- **Portable Design**: Can be packaged into a standalone EXE (Windows).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/yiyus-toolbox.git
    cd yiyus-toolbox
    ```

2.  **Install Dependencies**:
    Requires Python 3.8+ (Tested on 3.11).
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You need `torch`, `opencv-python`, and `PyQt5`.*

3.  **Run dependencies**:
    Ensure you have the LaMa model file `big-lama.pt` in the `model/` directory.

## Usage

### Run from Source
```bash
run_source.bat
# OR
python src/demo.py
```

### Operations
- **Load Image**: Click the Orange button.
- **Draw Mask**: Left-click and drag to cover the watermark.
- **Adjust Brush**: Use the slider.
- **Move/Zoom**: Scroll to zoom, Middle-click to drag.
- **Start**: Click the Green button to process the single image.
- **Batch Mode**: Click the Blue button, select a folder, allow it to load the first image, draw the mask, then click Start.

- **Video Splitter**:
    1. Switch to the **"Video Auto Shot Splitter"** tab.
    2. Click **"Select Folder"** (Blue button) to choose the directory containing videos.
    3. Select a Snapshot Mode (Start/Middle/End/Average).
    4. Click **"Start Split & Save"** (Green button) to process all videos automatically.

## Output Directories

To keep the source folder clean, all processing results are saved in automatically created subdirectories:

- **Single/Batch Image Inpainting**: Results saved in `images_output_yiyu_box` inside the source folder.
- **Video Splitter**: Results saved in `videos_output_yiyu_box` inside the source video folder.

## Acknowledgements

- Original Author: **zhaoyun007** (52pojie.cn)
- Model: [LaMa (Resolution-robust Large Mask Inpainting with Fourier Convolutions)](https://github.com/advimman/lama)

## License

This project is for educational and personal use. Please respect the license of the original LaMa model and the original author.
