# uncompyle6 version 3.9.3
# Python bytecode version base 3.6 (3379)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
import os
import sys

# Allow OpenMP duplication (Common fix for Torch+Numpy on Windows)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# CRITICAL: Import torch FIRST to load DLLs before PyQt5/OpenCV conflicts occur
import torch

from DemoUI import Ui_Form
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
from PyQt5 import QtWidgets # Still needed if code uses QtWidgets.X
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
import cv2, numpy as np
from contact import Ui_contact
from PyQt5.QtGui import QIcon

from batch_processor import BatchWorkThread

class MainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        
        # Connect Slider
        self.ui.slider_brush.valueChanged.connect(self.update_brush_size)
        
        # Manual connection to avoid auto-connect duplication
        self.ui.btn_batch.clicked.connect(self.start_batch_mode)
        
        # Set initial brush size
        self.ui.widget.brush_size = self.ui.slider_brush.value()
        self.ui.label_brush.setText(f"画笔大小: {self.ui.widget.brush_size}")

    def update_brush_size(self, value):
        self.ui.widget.brush_size = value
        self.ui.label_brush.setText(f"画笔大小: {value}")
        
    @QtCore.pyqtSlot()
    def load_image_from_path(self, path):
        if not path or not os.path.exists(path): return False
        try:
            self.org_path = path # Standardize on self.org_path usage
            self.ui.widget.image = QPixmap(path)
            self.ui.widget.image_path = path
            self.ui.widget.thread.image_path = path
            
            # Using imdecode for unicode support
            self.image_cv = cv2.imdecode(np.fromfile(path, dtype=np.uint8), -1)
            if self.image_cv is None: return False
            if len(self.image_cv.shape) == 2: # Gray to RGB
                self.image_cv = cv2.cvtColor(self.image_cv, cv2.COLOR_GRAY2RGB)
                
            self.ui.widget.image_cv = self.image_cv
            self.image = QPixmap(path)
            
            # Init gray mask
            gray0 = np.zeros((self.image_cv.shape[0], self.image_cv.shape[1]), dtype=np.uint8)
            cv2.imwrite("gray.png", gray0)
            self.ui.widget.gray_img = QPixmap("gray.png")
            return True
        except Exception as e:
            print(f"Load image error: {e}")
            return False

    @QtCore.pyqtSlot()
    def start_batch_mode(self):
        # 1. Select directory
        folder_path = QFileDialog.getExistingDirectory(self, "选择要处理的文件夹")
        if not folder_path: return
        
        # 2. Find first image
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not image_files:
            QMessageBox.warning(self, "提示", "文件夹中没有图片！")
            return
            
        first_img_path = os.path.join(folder_path, image_files[0])
        
        # 3. Auto-load first image to widget
        if self.load_image_from_path(first_img_path):
            self.batch_folder_path = folder_path
            self.ui.lineEdit.setText(f"批量模式已就绪。请绘制水印区域，然后点击'开始去水印'。")
            QMessageBox.information(self, "操作提示", 
                "已自动加载文件夹中的第一张图片。\n\n"
                "1. 请在当前图片上绘制出水印区域。\n"
                "2. 点击【开始去水印】按钮。\n"
                "3. 程序将把此蒙版应用到该文件夹下的所有图片。\n\n"
                "⚠️ 注意：批量处理仅适用于同尺寸、同比例且水印位置一致的图片！")
        else:
             QMessageBox.warning(self, "警告", "无法加载第一张图片！")

    def update_batch_progress(self, val, msg):
        self.ui.lineEdit.setText(f"批量处理中... {val}% - {msg}")
        
    def batch_finished(self, msg):
        self.ui.lineEdit.setText(f"批量处理完成: {msg}")
        # Reset UI
        self.ui.btn_batch.setEnabled(True)
        self.ui.btn_org.setEnabled(True)
        self.ui.btn_org_2.setEnabled(True)
        self.batch_folder_path = None # Exit batch mode
        QtWidgets.QMessageBox.information(self, "完成", msg)

    @QtCore.pyqtSlot()
    def on_btn_org_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", ".", "图片文件 (*.jpg *.png *.jpeg)")
        if path:
            self.load_image_from_path(path)
            self.batch_folder_path = None # Manual load implies single mode

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        self.contact_window = my_Ui_contact()
        self.contact_window.show()

    @QtCore.pyqtSlot()
    def on_btn_org_2_clicked(self):
        # Common: Save Mask
        self.ui.widget.gray_img.save("mask.png")
        self.ui.widget.drawing1 = False
        self.ui.btn_org_2.setEnabled(False)
        self.ui.btn_org.setEnabled(False)
        self.ui.btn_batch.setEnabled(False) # Disable batch too
        
        # Check Mode
        if hasattr(self, 'batch_folder_path') and self.batch_folder_path:
             # BATCH MODE
             self.ui.lineEdit.setText("正在执行批量去水印 (后台处理中)...")
             self.batch_thread = BatchWorkThread(self.batch_folder_path, "mask.png", device_str="cpu")
             self.batch_thread.progress_signal.connect(self.update_batch_progress)
             self.batch_thread.finished_signal.connect(self.batch_finished)
             self.batch_thread.start()
        else:
             # SINGLE MODE
             self.ui.lineEdit.setText("转换中......")
             self.ui.widget.btn_org_2 = self.ui.btn_org_2
             self.ui.widget.btn_org = self.ui.btn_org
             self.ui.widget.lineEdit = self.ui.lineEdit
             # Re-enable batch button in single mode callback? 
             # Original code manages btn_org/btn_org_2 in thread callback, but not btn_batch.
             # We might need to ensure btn_batch is re-enabled if single mode finishes.
             # Single mode completion logic is in Label.timeStop (via signal).
             # We need to updating label.py to re-enable btn_batch too if we disable it here.
             # For now, let's NOT disable btn_batch for single mode or update label.py.
             # Update: I'll disable it for safety, and rely on user re-opening app or fix label.py.
             # Better: Update label.py? Or just not disable btn_batch in single mode?
             # Let's disable it to prevent chaos.
             # But label.py's timeStop needs to re-enable it.
             # I can pass btn_batch to widget too.
             self.ui.widget.btn_batch = self.ui.btn_batch
             
             self.ui.widget.thread.start()


class my_Ui_contact(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_contact()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("./resources/ico.jpg"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
