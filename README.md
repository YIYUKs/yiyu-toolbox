# Yiyu's Toolbox (乙羽的工具箱)

[中文文档](README_CN.md)

A local, offline AI-powered tool for watermark removal, background removal, video splitting, and image upscaling based on the LaMa (Large Mask Inpainting) model.

This project is a refactor and enhancement of the "AI Magic Eraser" originally by **zhaoyun007**.

Future features will be integrated based on personal requirements.

- **Premium UI System**:
    - **Dark Mode**: Ergonomic dark theme for professional work and reduced eye strain.
    - **Dual Progress Bars**: Real-time monitoring of both "Total Progress" and "Current Item Progress". No more "black box" waiting.
    - **Consistent Layout**: Unified vertical flow across all modules for a seamless user experience.
- **Portability**: Supports packaging as a fully standalone "Green Version" EXE.

## 🚀 Release v1.0 (Latest)

**Version 1.0.0 (2026-01-02)**
- **UI Redesign**: Brand new Dark Mode skin with a dedicated `StyleManager`.
- **Feedback Loop**: Introduced the Dual Progress Bar mechanism for better task transparency.
- **Stability Fixes**: Refined portable build scripts to resolve DLL relocation issues (WinError 1114).
- **UX Refinement**: Streamlined the Watermark tab layout for more intuitive operation.

## Installation & Run

1. **Environment**:
   Python 3.8+ (Development environment: 3.11).
   ```bash
   pip install -r requirements.txt
   ```
   *Main dependencies: `torch`, `opencv-python`, `PyQt5`*

2. **Model Files**:
   Ensure `model/big-lama.pt` exists.

3. **Start**:
   ```bash
   # Windows users can run directly:
   run_source.bat
   
   # Or:
   python src/demo.py
   ```

## Build Portable Version (EXE)

To generate a standalone green portable version:

1. Ensure `resources/icon.ico` exists (optional for icon).
2. Run `create_portable_version.bat`.
3. Wait for completion; `yiyu_toolbox_portable` folder will be generated.
4. Run `乙羽的工具箱.exe` inside that folder.

## Usage Guide

- **Auto Watermark Removal**:
    1. Click **"Select Image"** (Orange button).
    2. Paint the removal area. Adjust brush size with the slider, zoom/pan with the mouse.
    3. Click **"Start Removal"** (Green button).

- **Batch Processing**:
    1. Click **"Batch Processing (Fixed Position)"** (Blue button).
    2. Select image folder.
    3. Draw the mask on the first loaded image.
    4. Click **"Start Removal"**.
    *Note: Only for images with identical resolution and watermark position.*

- **Video Splitter**:
    1. Switch to the **"Get Video Scenes"** tab.
    2. Click **"Select Folder"** (Blue button).
    3. Choose a mode (Start/Middle/End/Average).
    4. Click **"Start Split & Save"** (Green button).

- **90-Point Automatic Matting**:
    1. Switch to the **"90-Point Automatic Matting"** tab.
    2. Select image or folder.
    3. Select **Edge Strength** (High is recommended).
    4. Click **"Auto Matting"**. Results saved as transparent PNG.

- **90-Point Image Upscaling**:
    1. Switch to the **"90-Point Image Upscaling"** tab.
    2. Select image or folder.
    3. Choose **AI Model**: "General" for photos, "Anime" for illustrations.
    4. Click **"AI One-Click Upscale"**. Initial run will download weights.

## Output Directories

To keep folders clean, results are saved in auto-created subdirectories:

- **Watermark Removal**: Saved in `images_output_yiyu_box`.
- **Video Splitter**: Saved in `videos_output_yiyu_box`.
- **AI Upscaling**: Saved in `upscale_output_yiyu_box`.

## Acknowledgements & Open Source Credits

This project integrates the following outstanding open-source projects:

- **Core Models**:
    - [LaMa](https://github.com/advimman/lama): Powerful frequency-aware AI inpainting.
    - [BiRefNet](https://github.com/ZhengPeng7/BiRefNet): High-precision matting network.
    - [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN): State-of-the-art super-resolution.
- **Libraries**:
    - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/): Python GUI framework.
    - [PyTorch](https://pytorch.org/): Deep learning inference engine.
    - [OpenCV](https://opencv.org/): Image processing & Guided Filter algorithms.
    - [PySceneDetect](https://github.com/Breakthrough/PySceneDetect): Video scene detection.
    - [rembg](https://github.com/danielgatis/rembg): Background removal wrapper.
- **Credits**:
    - **zhaoyun007** (52pojie.cn)

## License

Personal and educational use only. Please respect the licenses of the original models and authors.
