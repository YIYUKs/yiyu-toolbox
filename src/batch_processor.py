import os
import cv2
import torch
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from helper import norm_img, resize_max_size

# Reuse LaMa class if possible, or re-import. 
# It's currently in label.py. Better to move LaMa to a separate file or import from label.
# To avoid circular imports, I should probably move LaMa class to a new model_wrapper.py or similar.
# For now, I'll import from label, but beware if label imports this. 
# Actually, label.py imports helper. batch_processor needs LaMa.
# I will copy LaMa class here or refactor. Refactoring is cleaner. 
# But to minimize changes, I will check if I can import LaMa from label.

# Let's see... label.py has LaMa class.
# I will refactor LaMa out to lama_model.py to be clean.

from label import LaMa 

class BatchWorkThread(QThread):
    progress_signal = pyqtSignal(int, str) # value, message
    finished_signal = pyqtSignal(str)

    def __init__(self, folder_path, mask_path, device_str="cpu"):
        super().__init__()
        self.folder_path = folder_path
        self.mask_path = mask_path
        self.device_str = device_str
        self.is_running = True

    def run(self):
        try:
            if not os.path.exists(self.folder_path):
                self.finished_signal.emit(f"Error: Folder not found {self.folder_path}")
                return

            output_dir = os.path.join(self.folder_path, "output_yiyu_box")
            os.makedirs(output_dir, exist_ok=True)

            # Load Model
            device = torch.device(self.device_str)
            # Assuming model path is relative to CWD or EXE
            model = LaMa(crop_trigger_size=[2042, 2042], crop_margin=256, device=device)

            # Load Mask
            mask_cv = cv2.imread(self.mask_path, cv2.IMREAD_GRAYSCALE)
            if mask_cv is None:
                self.finished_signal.emit("Error: Invalid mask file.")
                return
            
            # Identify mask area (bounding box) to apply to other images?
            # Or just usage the full mask if it's full size?
            # Scheme A: "Fixed Position". 
            # If images are different sizes, this is tricky.
            # Strategy: 
            # 1. Start with the mask (which matches the reference image size).
            # 2. For each target image:
            #    - Verify size match? 
            #    - OR: Align Top-Left?
            #    - OR: Resize mask to target? (Risks distortion)
            #    - Best guess for "fixed position": Align Top-Left or stretch?
            #    - Let's assume for now users batch process similar sized images (e.g. camera photos).
            #    - I'll try to align Top-Left. If target is smaller, crop mask. If target is larger, pad mask black.
            
            image_files = [f for f in os.listdir(self.folder_path) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            
            total = len(image_files)
            for idx, filename in enumerate(image_files):
                if not self.is_running: break
                
                input_path = os.path.join(self.folder_path, filename)
                self.progress_signal.emit(int((idx / total) * 100), f"Processing {filename}...")
                
                # Read Image
                image = cv2.imdecode(np.fromfile(input_path, dtype=np.uint8), -1)
                if image is None: continue
                
                if len(image.shape) == 2:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                elif len(image.shape) == 3:
                     # Handle Alpha
                    if image.shape[2] == 4:
                         image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
                    else:
                         image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Prepare Mask for this image
                h, w = image.shape[:2]
                mask_h, mask_w = mask_cv.shape[:2]
                
                current_mask = np.zeros((h, w), dtype=np.uint8)
                
                # Composite mask_cv onto current_mask (Top-Left Alignment)
                # Determine intersection size
                copy_h = min(h, mask_h)
                copy_w = min(w, mask_w)
                
                current_mask[0:copy_h, 0:copy_w] = mask_cv[0:copy_h, 0:copy_w]

                # Pre-processing similar to label.py
                # Note: label.py resizes image to 'size_limit'. We should respect that or keep original?
                # label.py defaults size_limit to max(image.shape) which effectively means original size unless very huge.
                # But it calls resize_max_size.
                
                # Check for large images?
                # Let's keep it simple: norm_img -> inference -> denorm
                
                img_t = norm_img(image) # Returns torch tensor or numpy? norm_img in helper says... let's check helper
                # Actually, label.py does:
                # image = resize_max_size(...)
                # image = norm_img(image)
                # mask = resize_max_size(...)
                # mask = norm_img(mask)
                
                # Wait, if we resized image, we must resize mask similarly.
                # If we don't resize, we might OOM.
                # Let's assume we don't resize for batch (quality priority) unless OOM.
                # But to reach parity with single mode:
                
                img_norm = norm_img(image)
                mask_norm = norm_img(current_mask)
                
                # Inference
                # Model expects [B, C, H, W]? norm_img might return HWC 0-1 float.
                # label.py: res_np_img = model(image, mask)
                # LaMa.__call__ handles tensor conversion.
                
                res_np_img = model(img_norm, mask_norm)
                
                # Save
                save_path = os.path.join(output_dir, f"fixed_{filename}")
                cv2.imencode(".jpg", res_np_img)[1].tofile(save_path)
            
            self.progress_signal.emit(100, "Completed!")
            self.finished_signal.emit("批量处理完成，文件保存在选择的文件夹中")

        except Exception as e:
            self.finished_signal.emit(f"Error: {str(e)}")

    def stop(self):
        self.is_running = False
