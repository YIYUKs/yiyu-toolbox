# AI Readiness Guide: Yiyu's Toolbox (乙羽工具箱)

> **Purpose**: This document provides high-level context, architectural understanding, and long-term goals for AI agents (and human developers) working on this project. It is designed to be machine-parsable and concise.

## 1. Project Identity
*   **Name**: Yiyu's Toolbox (乙羽工具箱) / AI Watermark Remover
*   **Type**: Desktop Application (Windows)
*   **Core Function**: Offline image inpainting (watermark removal) using Deep Learning (LaMa).
*   **Key Constraint**: Must work offline without external API dependencies.

## 2. Technical Stack
*   **Language**: Python 3.8+
*   **GUI Framework**: PyQt5
*   **Computer Vision**: OpenCV (`cv2`), NumPy
*   **Deep Learning**: PyTorch (`torch`)
    *   **Model Architecture**: LaMa (Large Mask Inpainting with Fourier Convolutions)
    *   **Weights**: `./model/big-lama.pt` (TorchScript format recommended)

## 3. Codebase Map
| File Path | Component | Responsibility | AI Note |
| :--- | :--- | :--- | :--- |
| `src/demo.py` | **Entry Point** | Main Window, Slot/Signal connections, UI initialization. | logic is somewhat monolithic here. |
| `src/label.py` | **Widget & Logic** | Custom `Label` widget for painting masks. Contains `LaMa` model wrapper. | **Refactor Candidate**: `LaMa` class should ideally be moved to a standalone `engine` module. |
| `src/video_splitter.py` | **Feature** | Video scene detection and frame extraction thread. | Supports both Single and Batch folder modes. |
| `src/video_ui.py` | **UI** | Widget for Video Splitter tab. | |
| `src/batch_processor.py` | **Feature** | `BatchWorkThread` for folder-level processing. | Currently naive implementation (applies same mask coord to all images). |
| `src/helper.py` | **Utils** | Image resizing (`resize_max_size`), Normalization (`norm_img`), Padding. | Standard CV utils. |
| `build_exe.bat` | **Deploy** | PyInstaller build script. | Check `*.spec` for build config. |

## 4. Key Logic & Patterns
*   **Inference Flow**:
    1.  User loads image -> `QPixmap` displayed in `Label`.
    2.  User paints mask -> Drawn on both visual `image` (white) and logical `gray_img` (mask).
    3.  `start` triggered -> Image & Mask resized/padded -> LaMa Model Inference -> Result displayed.
*   **Concurrency**:
    *   Long-running tasks (Inference, Video Split) **MUST** run in `QThread` to avoid freezing the UI.
    *   Signals (`pyqtSignal`) used to update UI from threads.
*   **Standardized Output**:
    *   Images -> `images_output_yiyu_box`
    *   Videos -> `videos_output_yiyu_box`

## 5. Development Roadmap
*(Updated: 2025-12-20)*

- [x] **Core Functionality**: Single image removal working.
- [x] **Video Integration**: Video Auto Shot Splitter integrated.
- [x] **Batch Processing**:
    - [x] Batch Image (Fixed Position)
    - [x] Batch Video (Folder Scan)
- [x] **UX Improvements**:
    - [x] Tabbed Interface & Button Styling
    - [x] No-Popup Workflow (Silent completion)
    - [x] Standardized Output Directories
- [x] **Distribution**: Build script usage verified.
- [ ] **Refactoring**: Move `LaMa` class out of UI code (`label.py`).

## 6. AI Agent Guidelines
*   **Context**: When asked about the "Web App", clarify that this repo (`l:\乙羽工具箱`) is the **Offline Client**. The Web App is a separate project (not currently in this workspace).
*   **Conventions**: 
    *   Prefer **Chinese** for user communication.
    *   Code comments in English or Chinese are acceptable (consistency preferred).
    *   **Always** check `requirements.txt` before suggesting new imports.
*   **Pitfalls**:
    *   `cv2` reads as BGR, `PyQt` expects RGB. Watch out for channel swapping (`cv2.cvtColor`).
    *   Windows paths can be tricky with backslashes; use `os.path.join` or raw strings.
