# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-01-02

### Added
- **Global Theme**: Implemented a professional Dark Mode theme using a centralized `StyleManager`.
- **Dual Progress Bars**: Added global progress tracking (Total and Item level) in the main window for all processing tasks.
- **Enhanced Matting**: Integrated BiRefNet model with Guided Filter for high-precision edge processing.
- **Image Upscaling**: Added Real-ESRGAN support with tiling for large image processing.
- **Video Splitting**: Batch processing for video scene extraction with multiple frame-seeking modes.

### Changed
- **UI Architecture**: Refactored `DemoUI.py` and other UI modules to use a consistent vertical stack layout.
- **Portable Build**: Developed `create_portable_version.bat` to create a stable, self-contained environment with a C# launcher.
- **Watermark UX**: Simplified selection and brush control layouts for intuitive painting.

### Fixed
- **DLL Loading Errors**: Resolved recurring `WinError 1114` issues in PyInstaller builds by switching to a portable runtime strategy.
- **UI Logic**: Fixed various signal-slot connection issues during batch processing.

---
*Created by Antigravity AI for Yiyu's Toolbox.*
