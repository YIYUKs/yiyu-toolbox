# uncompyle6 version 3.9.3
# Python bytecode version base 3.6 (3379)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: label.py
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QPen
import time
from helper import norm_img, resize_max_size
from typing import List
import cv2, torch, numpy as np
from helper import pad_img_to_modulo, boxes_from_mask
from PyQt5.QtCore import QThread, pyqtSignal
import os

class LaMa:

    def __init__(self, crop_trigger_size: List[int], crop_margin: int, device):
        self.crop_trigger_size = crop_trigger_size
        self.crop_margin = crop_margin
        self.device = device
        # Model is in ../model/relative to this file (yiyu Toolbox core/model/)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "model", "big-lama.pt")
        model = torch.jit.load(model_path, map_location="cpu")
        model = model.to(device)
        model.eval()
        self.model = model

    @torch.no_grad()
    def __call__(self, image, mask):
        area = image.shape[1] * image.shape[2]
        if area < self.crop_trigger_size[0] * self.crop_trigger_size[1]:
            return self._run(image, mask)
        else:
            print("Trigger crop image")
            boxes = boxes_from_mask(mask)
            crop_result = []
            for box in boxes:
                crop_image, crop_box = self._run_box(image, mask, box)
                crop_result.append((crop_image, crop_box))

            image = (image.transpose(1, 2, 0) * 255).astype(np.uint8)[:, :, ::-1]
            for crop_image, crop_box in crop_result:
                x1, y1, x2, y2 = crop_box
                image[y1:y2, x1:x2, :] = crop_image

            return image

    def _run_box(self, image, mask, box):
        box_h = box[3] - box[1]
        box_w = box[2] - box[0]
        cx = (box[0] + box[2]) // 2
        cy = (box[1] + box[3]) // 2
        img_h, img_w = image.shape[1:]
        w = box_w + self.crop_margin * 2
        h = box_h + self.crop_margin * 2
        l = max(cx - w // 2, 0)
        t = max(cy - h // 2, 0)
        r = min(cx + w // 2, img_w)
        b = min(cy + h // 2, img_h)
        crop_img = image[:, t:b, l:r]
        crop_mask = mask[:, t:b, l:r]
        print(f"box size: ({box_h},{box_w}) crop size: {crop_img.shape}")
        return (
         self._run(crop_img, crop_mask), [l, t, r, b])

    def _run(self, image, mask):
        """
        image: [C, H, W] RGB
        mask: [1, H, W]
        return: BGR IMAGE
        """
        device = self.device
        origin_height, origin_width = image.shape[1:]
        image = pad_img_to_modulo(image, mod=8)
        mask = pad_img_to_modulo(mask, mod=8)
        mask = (mask > 0) * 1
        image = torch.from_numpy(image).unsqueeze(0).to(device)
        mask = torch.from_numpy(mask).unsqueeze(0).to(device)
        inpainted_image = self.model(image, mask)
        cur_res = inpainted_image[0].permute(1, 2, 0).detach().cpu().numpy()
        cur_res = cur_res[0:origin_height, 0:origin_width, :]
        cur_res = np.clip(cur_res * 255, 0, 255).astype("uint8")
        cur_res = cv2.cvtColor(cur_res, cv2.COLOR_RGB2BGR)
        return cur_res


class WorkThread(QThread):
    progress_signal = pyqtSignal(int, int, str)
    my_signal = pyqtSignal(str)

    def __int__(self):
        super(WorkThread, self).__init__()

    def process(self):
        try:
            device = torch.device("cpu")
            input_image_path = self.image_path
            if not input_image_path or not os.path.exists(input_image_path):
                print(f"Error: Input path invalid: {input_image_path}")
                return

            self.progress_signal.emit(10, 10, "正在初始化模型...")
            model = LaMa(crop_trigger_size=[2042, 2042], crop_margin=256, device=device)
            input = input_image_path
            
            # Resolve mask_pic path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mask_pic = os.path.join(base_dir, "mask.png")
            
            self.progress_signal.emit(20, 20, "正在读取图片...")
            image = cv2.imdecode(np.fromfile(input, dtype=(np.uint8)), -1)
            if image is None: 
                print(f"Error: Failed to decode image: {input}")
                return

            if len(image.shape) == 3:
                if image.shape[2] == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
                else:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                original_shape = image.shape
                interpolation = cv2.INTER_CUBIC
                size_limit = "Original"
                if size_limit == "Original":
                    size_limit = max(image.shape)
            else:
                size_limit = int(size_limit)
            
            print(f"Origin image shape: {original_shape}")
            image = resize_max_size(image, size_limit=size_limit, interpolation=interpolation)
            print(f"Resized image shape: {image.shape}")
            image = norm_img(image)
            
            self.progress_signal.emit(40, 40, "正在处理蒙版...")
            mask = cv2.imread(mask_pic, cv2.IMREAD_GRAYSCALE)
            if mask is None:
                 print(f"Error: Failed to read mask: {mask_pic}")
                 return
                 
            mask = resize_max_size(mask, size_limit=size_limit, interpolation=interpolation)
            mask = norm_img(mask)
            
            self.progress_signal.emit(50, 50, "AI 正在修复图片...")
            start = time.time()
            res_np_img = model(image, mask)
            print(f"process time: {(time.time() - start) * 1000}ms")
            
            torch.cuda.empty_cache()
            
            # Save to: <OriginalDir>/images_output_yiyu_box/<Filename>_magic.png
            original_dir = os.path.dirname(os.path.abspath(input_image_path))
            output_dir = os.path.join(original_dir, "images_output_yiyu_box")
            os.makedirs(output_dir, exist_ok=True)
            
            save_name = f"{os.path.basename(input_image_path)}_magic.png"
            save_path = os.path.join(output_dir, save_name)
            
            # Use imencode for unicode path support
            self.progress_signal.emit(90, 90, "正在保存结果...")
            success, encoded_img = cv2.imencode(".png", res_np_img)
            if success:
                 encoded_img.tofile(save_path)
            else:
                 print("Error: Failed to encode result image")
            self.progress_signal.emit(100, 100, "处理完毕")
        except Exception as e:
            print(f"WorkThread process error: {str(e)}")

    def run(self):
        try:
            self.process()
        finally:
            self.my_signal.emit("ok")


class Label(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(Label, self).__init__(parent)
        self.thread = WorkThread()
        self.thread.my_signal.connect(self.timeStop)
        self.drawing = False
        self.drawing1 = True
        self.image_path = None
        self.thread.image_path = None
        
        # Load images
        self.image_cv = None
        self.image = None
        self.gray_img = None

        # Interaction state
        
        # Interaction state
        self.lastPoint = QtCore.QPoint()
        self.brush_size = 20
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.is_panning = False
        self.pan_start = QPoint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        
        # Calculate display rect based on offset and scale
        if self.image is None or self.image.isNull(): 
             painter.setPen(QPen(Qt.gray, 20))
             font = QtGui.QFont()
             font.setPointSize(20)
             painter.setFont(font)
             painter.drawText(self.rect(), Qt.AlignCenter, "请加载图片")
             return

        # Draw the image
        scaled_w = int(self.image.width() * self.scale_factor)
        scaled_h = int(self.image.height() * self.scale_factor)
        
        # Center if smaller than widget
        if scaled_w < self.width() and scaled_h < self.height():
             # Reset offset to center if it fits fully
             # Or just allow moving freely? Let's just draw at offset.
             pass
        
        target_rect = QtCore.QRect(self.offset.x(), self.offset.y(), scaled_w, scaled_h)
        painter.drawPixmap(target_rect, self.image)

    def wheelEvent(self, event):
        if self.image is None: return
        angle = event.angleDelta().y()
        old_scale = self.scale_factor
        if angle > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor *= 0.9
        
        # Limit scale
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
        
        # Adjust offset to zoom towards mouse position?
        # Simple zoom for now:
        # To zoom towards mouse: 
        # new_mouse_pos_rel_image = (mouse_pos - new_offset) / new_scale
        # old_mouse_pos_rel_image = (mouse_pos - old_offset) / old_scale
        # we want these equal.
        
        cursor_pos = event.pos()
        rel_x = (cursor_pos.x() - self.offset.x()) / old_scale
        rel_y = (cursor_pos.y() - self.offset.y()) / old_scale
        
        new_offset_x = cursor_pos.x() - rel_x * self.scale_factor
        new_offset_y = cursor_pos.y() - rel_y * self.scale_factor
        
        self.offset = QPoint(int(new_offset_x), int(new_offset_y))
        
        self.update()



    def draw_point(self, pos):
        # Convert widget coordinates to image coordinates
        img_x = int((pos.x() - self.offset.x()) / self.scale_factor)
        img_y = int((pos.y() - self.offset.y()) / self.scale_factor)
        
        self.nowPoint = QPoint(img_x, img_y)
        
        # Draw on self.image (Display)
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setPen(QPen(Qt.white, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPoint(self.nowPoint)
        painter.end() # Important to close painter

        # Draw on self.gray_img (Mask)
        painter_mask = QPainter(self.gray_img)
        painter_mask.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter_mask.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter_mask.setPen(QPen(Qt.white, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter_mask.drawPoint(self.nowPoint)
        painter_mask.end()

        # Connect lines if fast movement? 
        # The original code used drawEllipse for points, which is disconnected.
        # QPainter.drawLine to lastPoint would be smoother.
        # Let's add that improvement.
        
        if not self.lastPoint.isNull() and self.drawing:
             # We need to store lastPoint in Image Coordinates, not Widget Coordinates
             pass 
        
        # For simple point drawing (continuous):
        # Actually logic above is mostly fine, but drawPoint might be sparse.
        # Let's stick to drawPoint for now to match original logic but with dynamic size.
        # Or better: use drawLine from last known image point.
        
        self.update()

    # Redefining mousePress to clearer logic for Line drawing
    def mousePressEvent(self, event):
        if self.image is None: return
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = True
            # Calculate initial point
            img_x = int((event.pos().x() - self.offset.x()) / self.scale_factor)
            img_y = int((event.pos().y() - self.offset.y()) / self.scale_factor)
            self.last_img_point = QPoint(img_x, img_y)
            self.paint_on_image(self.last_img_point, self.last_img_point)
        elif event.button() == QtCore.Qt.MidButton:
            self.is_panning = True
            self.pan_start = event.pos()
        elif event.button() == QtCore.Qt.RightButton:
            # Clear drawing (Reset mask and image)
            # Reset Gray Mask
            gray0 = np.zeros((self.image_cv.shape[0], self.image_cv.shape[1]), dtype=(np.uint8))
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            gray_path = os.path.join(base_dir, "gray.png")
            cv2.imwrite(gray_path, gray0)
            self.gray_img = QPixmap(gray_path)
            
            # Reset Display Image (Reload from source to remove lines)
            self.image = QPixmap(self.image_path)
            
            self.update()
            print("Drawing cleared!")

    def mouseMoveEvent(self, event):
        if self.image is None: return
        if event.buttons() & Qt.LeftButton and self.drawing and self.drawing1:
            img_x = int((event.pos().x() - self.offset.x()) / self.scale_factor)
            img_y = int((event.pos().y() - self.offset.y()) / self.scale_factor)
            curr_img_point = QPoint(img_x, img_y)
            
            self.paint_on_image(self.last_img_point, curr_img_point)
            self.last_img_point = curr_img_point
            
        elif event.buttons() & Qt.MidButton and self.is_panning:
            delta = event.pos() - self.pan_start
            self.offset += delta
            self.pan_start = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = False
        elif event.button() == QtCore.Qt.MidButton:
            self.is_panning = False

    def paint_on_image(self, p1, p2):
        # Helper to draw line on both images
        for target in [self.image, self.gray_img]:
            painter = QPainter(target)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(Qt.white, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(p1, p2)
            painter.end()
        self.update()

    def timeStop(self, str):
        try:
            self.drawing1 = True
            if str == "ok":
                # Re-create fresh gray mask for next run
                gray0 = np.zeros((self.image_cv.shape[0], self.image_cv.shape[1]), dtype=(np.uint8))
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                gray_path = os.path.join(base_dir, "gray.png")
                cv2.imwrite(gray_path, gray0)
                self.gray_img = QPixmap(gray_path)
                
                # Resolve new image path
                original_dir = os.path.dirname(os.path.abspath(self.image_path))
                save_name = f"{os.path.basename(self.image_path)}_magic.png"
                new_path = os.path.join(original_dir, "images_output_yiyu_box", save_name)

                if os.path.exists(new_path):
                     self.image = QPixmap(new_path)
                     self.image_path = new_path # Update current path to result
                     self.thread.image_path = self.image_path
                     if hasattr(self, 'lineEdit'):
                          self.lineEdit.setText(f"转换完成，保存为【{os.path.basename(self.image_path)}】")
                else:
                     print(f"Error: Result file not found at {new_path}")
                     if hasattr(self, 'lineEdit'):
                          self.lineEdit.setText("转换完成，但未找到生成的文件。")
                
                self.update()
        except Exception as e:
            print(f"Label.timeStop error: {str(e)}")
        finally:
            # Re-enable parent buttons (Preferably from MainWindow via signal but keeping legacy support)
            if hasattr(self, 'btn_org_2'): self.btn_org_2.setEnabled(True)
            if hasattr(self, 'btn_org'): self.btn_org.setEnabled(True)
            if hasattr(self, 'btn_batch'): self.btn_batch.setEnabled(True)
